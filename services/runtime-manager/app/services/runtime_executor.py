from __future__ import annotations

import logging
import os
import shutil
import socket
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

import docker
from docker.errors import APIError, NotFound

from app.core.errors import RuntimeManagerError
from app.core.settings import Settings
from app.schemas.contracts import (
    ContainerStateResponse,
    DeleteContainerRequest,
    EnsureContainerRequest,
    StopContainerRequest,
)
from app.services.config_writer import prepare_runtime_dirs, write_openclaw_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeStoragePaths:
    container_root: str
    container_config: str
    container_workspace: str
    host_root: str
    host_config: str
    host_workspace: str


def _join_mount_path(base: str, *parts: str) -> str:
    if "\\" in base or (len(base) >= 2 and base[1] == ":"):
        return str(PureWindowsPath(base, *parts))
    return str(PurePosixPath(base, *parts))


class RuntimeExecutor:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._docker = docker.from_env()
        self._user_files_host_root: str | None = None

    def _internal_endpoint(self, runtime_id: str) -> str:
        return f"http://rt-{runtime_id}:18789"

    def _browser_url_from_container(self, container) -> str | None:
        container.reload()
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
        bindings = ports.get("18789/tcp")
        if not bindings:
            return None
        host_port = bindings[0].get("HostPort")
        if not host_port:
            return None

        browser_url = f"http://{self._settings.runtime_public_host}:{host_port}"
        try:
            result = container.exec_run(["cat", "/home/node/.openclaw/openclaw.json"], user="node")
            if result.exit_code == 0:
                import json

                config_content = result.output.decode()
                config = json.loads(config_content)
                gateway_token = config.get("gateway", {}).get("auth", {}).get("token")
                if gateway_token:
                    browser_url = f"{browser_url}/chat?session=main#token={gateway_token}"
        except Exception as exc:
            logger.error(f"Failed to read openclaw config: {exc}")

        return browser_url

    def _list_managed(self, runtime_id: str):
        return self._docker.containers.list(
            all=True,
            filters={
                "label": [
                    "clawloops.managed=true",
                    f"clawloops.runtimeId={runtime_id}",
                ]
            },
        )

    def _get_single_container(self, runtime_id: str):
        containers = self._list_managed(runtime_id)
        if len(containers) > 1:
            raise RuntimeManagerError(
                "RUNTIME_ACTION_CONFLICT",
                "multiple managed containers matched the same runtimeId",
                409,
            )
        return containers[0] if containers else None

    def _resolve_user_files_host_root(self) -> str:
        if self._settings.runtime_user_files_host_path:
            return self._settings.runtime_user_files_host_path
        if self._user_files_host_root is not None:
            return self._user_files_host_root

        mount_dir = self._settings.runtime_user_files_mount_dir.rstrip("/")
        # 使用容器名称而不是主机名，这样无论主机名是什么都能找到容器
        container_name = os.environ.get("RUNTIME_MANAGER_CONTAINER_NAME", "crewclaw-runtime-manager")

        try:
            container = self._docker.containers.get(container_name)
        except NotFound:
            # 如果通过名称找不到，尝试通过标签查找
            try:
                containers = self._docker.containers.list(filters={"label": "traefik.enable=true"})
                for c in containers:
                    if c.name == container_name:
                        container = c
                        break
            except Exception as e:
                logger.error(f"Failed to find container: {e}")
                raise RuntimeManagerError(
                    "RUNTIME_STORAGE_PATH_UNRESOLVED",
                    "failed to resolve runtime-manager container metadata for user-files mount",
                    500,
                ) from e

        if container is None:
            raise RuntimeManagerError(
                "RUNTIME_STORAGE_PATH_UNRESOLVED",
                "failed to resolve runtime-manager container metadata for user-files mount",
                500,
            )

        mounts = container.attrs.get("Mounts", []) or []
        for mount in mounts:
            if mount.get("Destination", "").rstrip("/") == mount_dir:
                source = mount.get("Source")
                if source:
                    self._user_files_host_root = source
                    return source

        # 如果找不到精确匹配，尝试查找父目录挂载
        parent_mount_dir = "/var/lib/clawloops"
        for mount in mounts:
            if mount.get("Destination", "").rstrip("/") == parent_mount_dir:
                source = mount.get("Source")
                if source:
                    # 构造完整的用户文件路径
                    full_source = f"{source}/user-files"
                    self._user_files_host_root = full_source
                    logger.info(f"Using parent mount {source} with user-files subdirectory")
                    return full_source

        raise RuntimeManagerError(
            "RUNTIME_STORAGE_PATH_UNRESOLVED",
            f"failed to resolve host source for mount {mount_dir} or parent {parent_mount_dir}",
            500,
        )

    def _resolve_runtime_storage_paths(self, user_id: str) -> RuntimeStoragePaths:
        container_root = _join_mount_path(self._settings.runtime_user_files_mount_dir, user_id)
        container_config = _join_mount_path(container_root, "openclaw-config")
        container_workspace = _join_mount_path(container_root, "workspace")

        host_root = _join_mount_path(self._resolve_user_files_host_root(), user_id)
        host_config = _join_mount_path(host_root, "openclaw-config")
        host_workspace = _join_mount_path(host_root, "workspace")

        return RuntimeStoragePaths(
            container_root=container_root,
            container_config=container_config,
            container_workspace=container_workspace,
            host_root=host_root,
            host_config=host_config,
            host_workspace=host_workspace,
        )

    def _container_mounts_match(self, container, paths: RuntimeStoragePaths) -> bool:
        container.reload()
        mounts = container.attrs.get("Mounts", []) or []
        mount_pairs = {(m.get("Source"), m.get("Destination")) for m in mounts}
        expected_pairs = {
            (paths.host_config, "/home/node/.openclaw"),
            (paths.host_workspace, "/home/node/.openclaw/workspace"),
        }
        return expected_pairs.issubset(mount_pairs)

    def _wait_ready(self, host: str, port: int) -> bool:
        deadline = time.time() + self._settings.runtime_startup_grace_seconds
        consecutive = 0
        while time.time() < deadline:
            try:
                with socket.create_connection((host, port), timeout=0.5):
                    consecutive += 1
            except OSError:
                consecutive = 0
            if consecutive >= self._settings.runtime_startup_consecutive_successes:
                return True
            time.sleep(self._settings.runtime_startup_poll_seconds)
        return False

    def _create_runtime_container(
        self,
        req: EnsureContainerRequest,
        labels: dict[str, str],
        alias: str,
        paths: RuntimeStoragePaths,
    ):
        try:
            logger.info(f"Pulling image: {self._settings.runtime_openclaw_image_ref}")
            self._docker.images.pull(self._settings.runtime_openclaw_image_ref)
            logger.info("Image pulled successfully")
        except Exception as exc:
            logger.error(f"Failed to pull image: {exc}")
            raise RuntimeManagerError(
                "RUNTIME_START_FAILED",
                f"failed to pull image: {str(exc)}",
                500,
            ) from exc

        command_parts = [part for part in self._settings.runtime_openclaw_command.split(" ") if part]
        if "--allow-unconfigured" not in command_parts:
            command_parts.append("--allow-unconfigured")
        logger.info(f"Using command: {command_parts}")

        container = self._docker.containers.create(
            image=self._settings.runtime_openclaw_image_ref,
            command=command_parts,
            labels=labels,
            environment={
                "HOME": "/home/node",
                "TERM": "xterm-256color",
                "TZ": "UTC",
                "OPENAI_BASE_URL": "http://litellm:4000",
            },
            volumes={
                paths.host_config: {"bind": "/home/node/.openclaw", "mode": "rw"},
                paths.host_workspace: {
                    "bind": "/home/node/.openclaw/workspace",
                    "mode": "rw",
                },
            },
            ports={"18789/tcp": None},
        )
        network = self._docker.networks.get(self._settings.runtime_openclaw_network)
        network.connect(container, aliases=[alias])
        container.start()
        return container

    def ensure_running(self, req: EnsureContainerRequest) -> ContainerStateResponse:
        try:
            logger.info(f"Starting ensure_running for runtime {req.runtimeId}")
            logger.info(f"Original compat config dir: {req.compat.openclawConfigDir}")
            logger.info(f"Original compat workspace dir: {req.compat.openclawWorkspaceDir}")

            paths = self._resolve_runtime_storage_paths(req.userId)
            logger.info(f"Resolved container storage root: {paths.container_root}")
            logger.info(f"Resolved host storage root: {paths.host_root}")

            prepare_runtime_dirs(paths.container_config, paths.container_workspace)

            is_windows = os.name == "nt"
            if not is_windows:
                import subprocess

                try:
                    subprocess.run(["chmod", "-R", "777", paths.container_root], check=True, capture_output=True)
                    logger.info(f"Set permissions to 777 for {paths.container_root}")
                except Exception as exc:
                    logger.warning(f"Failed to set permissions: {exc}")

            logger.info("Prepared runtime dirs")
            write_openclaw_config(paths.container_config, req.renderedConfig.openclawJson)

            if not is_windows:
                config_file = Path(paths.container_config) / "openclaw.json"
                if config_file.exists():
                    try:
                        os.chown(config_file, 1000, 1000)
                        config_file.chmod(0o666)
                        logger.info(f"Set permissions for config file: {config_file}")
                    except Exception as exc:
                        logger.warning(f"Failed to set config file permissions: {exc}")

            logger.info("Wrote openclaw config")

            def container_ip(container) -> str:
                container.reload()
                return (
                    container.attrs.get("NetworkSettings", {})
                    .get("Networks", {})
                    .get(self._settings.runtime_openclaw_network, {})
                    .get("IPAddress", "")
                )

            existing_containers = self._list_managed(req.runtimeId)
            container = None

            if existing_containers:
                container = existing_containers[0]
                container.reload()
                logger.info(f"Found existing container: {container.id}, status: {container.status}")

                if not self._container_mounts_match(container, paths):
                    logger.warning(
                        "Existing container mounts do not match resolved host paths; recreating container "
                        f"(runtimeId={req.runtimeId})"
                    )
                    container.remove(force=True)
                    container = None

            if container is not None:
                logger.info("Starting container with updated config")
                try:
                    logger.info(f"Container ID: {container.id}")
                    logger.info(f"Container status before start: {container.status}")
                    container.start()
                    container.reload()
                    logger.info(f"Container status after start: {container.status}")
                    logs = container.logs(tail=100).decode()
                    logger.info(f"Container logs: {logs}")
                except Exception as exc:
                    logger.error(f"Failed to start container: {exc}")
                    if "network" in str(exc) and "not found" in str(exc):
                        logger.info(
                            f"Network not found, recreating network: {self._settings.runtime_openclaw_network}"
                        )
                        try:
                            network = self._docker.networks.get(self._settings.runtime_openclaw_network)
                            logger.info(f"Network already exists: {self._settings.runtime_openclaw_network}")
                        except Exception:
                            network = self._docker.networks.create(
                                self._settings.runtime_openclaw_network,
                                driver="bridge",
                            )
                            logger.info(f"Created network: {self._settings.runtime_openclaw_network}")

                        alias = f"rt-{req.runtimeId}"
                        network.connect(container, aliases=[alias])
                        logger.info(f"Connected container to network: {self._settings.runtime_openclaw_network}")

            if container is None:
                logger.info("Creating new container")
                labels = {
                    "clawloops.managed": "true",
                    "clawloops.userId": req.userId,
                    "clawloops.runtimeId": req.runtimeId,
                    "clawloops.volumeId": req.volumeId,
                    "clawloops.routeHost": req.routeHost,
                    "clawloops.retentionPolicy": req.retentionPolicy,
                    "clawloops.configVersion": req.renderedConfig.configVersion,
                }
                alias = f"rt-{req.runtimeId}"
                container = self._create_runtime_container(req, labels, alias, paths)
                container.reload()
                logger.info(f"Created container with status: {container.status}")

                if container.status != "running":
                    logger.error(f"Container is not running, status: {container.status}")
                    try:
                        container.remove(force=True)
                        logger.info(f"Removed failed container: {container.id}")
                    except Exception as exc:
                        logger.error(f"Failed to remove failed container {container.id}: {exc}")
                    raise RuntimeManagerError("RUNTIME_START_FAILED", "container is not running", 500)

            ip = container_ip(container)
            logger.info(f"Container IP: {ip}")

            if not ip or not self._wait_ready(ip, 18789):
                logger.error("Failed to wait for container to be ready")
                raise RuntimeManagerError(
                    "RUNTIME_START_FAILED",
                    "failed to prepare config or start container",
                    500,
                )

            browser_url = self._browser_url_from_container(container)
            logger.info(f"Container browser URL: {browser_url}")

            return ContainerStateResponse(
                runtimeId=req.runtimeId,
                observedState="running",
                internalEndpoint=self._internal_endpoint(req.runtimeId),
                browserUrl=browser_url,
                message="creating",
            )
        except RuntimeManagerError:
            logger.exception("RuntimeManagerError occurred")
            raise
        except (APIError, OSError, ValueError) as exc:
            logger.exception(f"Exception occurred: {exc}")
            raise RuntimeManagerError(
                "RUNTIME_START_FAILED",
                f"failed to prepare config or start container: {str(exc)}",
                500,
            ) from exc

    def stop(self, req: StopContainerRequest) -> ContainerStateResponse:
        try:
            container = self._get_single_container(req.runtimeId)
            if container is None or container.status in {"exited", "created"}:
                return ContainerStateResponse(
                    runtimeId=req.runtimeId,
                    observedState="stopped",
                    message="already stopped",
                )
            container.stop(timeout=10)
            return ContainerStateResponse(runtimeId=req.runtimeId, observedState="stopped", message="stopped")
        except RuntimeManagerError:
            raise
        except (APIError, NotFound) as exc:
            raise RuntimeManagerError("RUNTIME_STOP_FAILED", "failed to stop container", 500) from exc

    def delete(self, req: DeleteContainerRequest) -> ContainerStateResponse:
        try:
            container = self._get_single_container(req.runtimeId)
            if container is not None:
                container.remove(force=True)
            if req.retentionPolicy == "wipe_workspace" and req.compat is not None:
                local_storage = self._resolve_runtime_storage_paths(req.userId).container_root
                if os.path.exists(local_storage):
                    shutil.rmtree(local_storage)
                    logger.info(f"Deleted local storage: {local_storage}")
            return ContainerStateResponse(runtimeId=req.runtimeId, observedState="deleted", message="deleted")
        except RuntimeManagerError:
            raise
        except (APIError, OSError) as exc:
            raise RuntimeManagerError(
                "RUNTIME_DELETE_FAILED",
                "failed to delete container or cleanup directories",
                500,
            ) from exc

    def get_state(self, runtime_id: str) -> ContainerStateResponse:
        container = self._get_single_container(runtime_id)
        if container is None:
            return ContainerStateResponse(
                runtimeId=runtime_id,
                observedState="deleted",
                internalEndpoint=None,
                message="not found as container fact",
            )
        status_map = {
            "running": "running",
            "exited": "stopped",
            "created": "creating",
            "paused": "error",
            "restarting": "creating",
            "dead": "error",
        }
        observed = status_map.get(container.status, "error")
        return ContainerStateResponse(
            runtimeId=runtime_id,
            observedState=observed,  # type: ignore[arg-type]
            internalEndpoint=self._internal_endpoint(runtime_id) if observed != "deleted" else None,
            browserUrl=self._browser_url_from_container(container) if observed != "deleted" else None,
            message="ok",
        )

    def _get_container_by_id(self, container_id: str):
        try:
            return self._docker.containers.get(container_id)
        except NotFound:
            raise RuntimeManagerError(
                "CONTAINER_NOT_FOUND",
                f"container not found: {container_id}",
                404,
            )

    def list_files(self, container_id: str, path: str) -> list[dict]:
        try:
            container = self._get_container_by_id(container_id)
            cmd = ["ls", "-la", path]
            result = container.exec_run(cmd, user="node")

            if result.exit_code != 0:
                raise RuntimeManagerError(
                    "FILE_LIST_FAILED",
                    f"failed to list files: {result.output.decode()}",
                    500,
                )

            lines = result.output.decode().split("\n")
            files = []
            for line in lines[1:-1]:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 9:
                    continue

                permissions = parts[0]
                name = " ".join(parts[8:])
                size = int(parts[4]) if parts[4].isdigit() else 0
                is_dir = permissions.startswith("d")

                if name in [".", ".."]:
                    continue

                files.append(
                    {
                        "name": name,
                        "path": f"{path}/{name}" if path != "/" else f"/{name}",
                        "type": "directory" if is_dir else "file",
                        "size": size,
                    }
                )

            return files
        except RuntimeManagerError:
            raise
        except Exception as exc:
            logger.exception("Failed to list files")
            raise RuntimeManagerError(
                "FILE_LIST_FAILED",
                f"failed to list files: {str(exc)}",
                500,
            ) from exc

    def read_file(self, container_id: str, path: str) -> str:
        try:
            container = self._get_container_by_id(container_id)
            cmd = ["cat", path]
            result = container.exec_run(cmd, user="node")

            if result.exit_code != 0:
                raise RuntimeManagerError(
                    "FILE_READ_FAILED",
                    f"failed to read file: {result.output.decode()}",
                    500,
                )

            return result.output.decode()
        except RuntimeManagerError:
            raise
        except Exception as exc:
            logger.exception("Failed to read file")
            raise RuntimeManagerError(
                "FILE_READ_FAILED",
                f"failed to read file: {str(exc)}",
                500,
            ) from exc

    def write_file(self, container_id: str, path: str, content: str) -> None:
        try:
            container = self._get_container_by_id(container_id)

            import tarfile
            from io import BytesIO

            file_dir = os.path.dirname(path)
            file_name = os.path.basename(path)
            content_bytes = content.encode("utf-8") if isinstance(content, str) else content

            tar_buffer = BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                tarinfo = tarfile.TarInfo(name=file_name)
                tarinfo.size = len(content_bytes)
                tarinfo.mtime = int(time.time())
                tarinfo.mode = 0o644
                tar.addfile(tarinfo, BytesIO(content_bytes))

            tar_buffer.seek(0)
            container.put_archive(file_dir, tar_buffer)
            logger.info(f"Successfully wrote file: {path}")
        except RuntimeManagerError:
            raise
        except Exception as exc:
            logger.exception("Failed to write file")
            raise RuntimeManagerError(
                "FILE_WRITE_FAILED",
                f"failed to write file: {str(exc)}",
                500,
            ) from exc
