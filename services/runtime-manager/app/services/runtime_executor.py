from __future__ import annotations

import logging
import re
import shutil
import socket
import time
from pathlib import Path

import docker
from docker.errors import APIError, ImageNotFound, NotFound

from app.core.errors import RuntimeManagerError
from app.core.settings import Settings
from app.schemas.contracts import (
    ContainerStateResponse,
    DeleteContainerRequest,
    EnsureContainerRequest,
    StopContainerRequest,
)
from app.services.config_writer import prepare_runtime_dirs, prepare_skill_dirs, write_openclaw_config
from app.services.drift_detector import detect_drift
from app.services.public_copy_sync import sync_public_copy_for_user
from app.services.skill_exporter import sync_skill_export
from app.services.skill_paths import container_workspace_skills_mount, skills_export_dir

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuntimeExecutor:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._docker = docker.from_env()

    def _internal_endpoint(self, runtime_id: str) -> str:
        return f"http://rt-{runtime_id}:18789"

    def _browser_url_from_route_host(self, route_host: str | None) -> str | None:
        if not route_host:
            return None
        scheme = (self._settings.runtime_browser_scheme or "https").strip().lower()
        if scheme not in {"http", "https"}:
            scheme = "https"
        return f"{scheme}://{route_host}"

    def _route_host_from_container(self, container) -> str | None:
        container.reload()
        labels = container.attrs.get("Config", {}).get("Labels", {}) or {}
        route_host = labels.get("clawloops.routeHost")
        if isinstance(route_host, str) and route_host.strip():
            return route_host.strip()
        return None

    def _router_name(self, runtime_id: str) -> str:
        safe_runtime_id = re.sub(r"[^a-z0-9-]+", "-", runtime_id.lower()).strip("-")
        safe_runtime_id = safe_runtime_id or "runtime"
        return f"openclaw-{safe_runtime_id}"

    def _with_traefik_labels(self, labels: dict[str, str], runtime_id: str, route_host: str) -> dict[str, str]:
        router_name = self._router_name(runtime_id)
        merged = dict(labels)
        merged["clawloops.routeHost"] = route_host
        merged["traefik.enable"] = "true"
        merged[f"traefik.http.routers.{router_name}.rule"] = f"Host(`{route_host}`)"
        merged[f"traefik.http.routers.{router_name}.entrypoints"] = "web"
        merged[f"traefik.http.services.{router_name}.loadbalancer.server.port"] = "18789"
        return merged

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

    def _create_runtime_container(self, req: EnsureContainerRequest, labels: dict[str, str], alias: str):
        self._ensure_runtime_image_available()
        
        volumes = {
            req.compat.openclawConfigDir: {"bind": "/home/node/.openclaw", "mode": "rw"},
            req.compat.openclawWorkspaceDir: {
                "bind": "/home/node/.openclaw/workspace",
                "mode": "rw",
            },
            str(skills_export_dir(req.userId)): {"bind": container_workspace_skills_mount(), "mode": "ro"},
        }

        container = self._docker.containers.create(
            image=self._settings.runtime_openclaw_image_ref,
            command=self._settings.runtime_openclaw_command.split(" "),
            labels=self._with_traefik_labels(labels, req.runtimeId, req.routeHost),
            environment={
                "HOME": "/home/node",
                "TERM": "xterm-256color",
                "TZ": "UTC",
                "OPENAI_BASE_URL": "http://litellm:4000",
            },
            volumes=volumes,
            ports={"18789/tcp": None},
        )
        try:
            network = self._docker.networks.get(self._settings.runtime_openclaw_network)
        except NotFound:
            network = self._docker.networks.create(
                name=self._settings.runtime_openclaw_network,
                driver="bridge",
            )
        network.connect(container, aliases=[alias])
        container.start()
        return container

    def _ensure_runtime_image_available(self) -> None:
        image_ref = self._settings.runtime_openclaw_image_ref
        try:
            self._docker.images.get(image_ref)
            logger.info("Using local runtime image: %s", image_ref)
            return
        except ImageNotFound:
            logger.info("Local runtime image not found, pulling: %s", image_ref)
        except APIError as exc:
            raise RuntimeManagerError(
                "RUNTIME_START_FAILED",
                f"failed to query local runtime image: {str(exc)}",
                500,
            ) from exc

        try:
            self._docker.images.pull(image_ref)
            logger.info("Pulled runtime image successfully: %s", image_ref)
        except Exception as exc:
            raise RuntimeManagerError(
                "RUNTIME_START_FAILED",
                (
                    "failed to pull runtime image. "
                    f"image={image_ref}. "
                    "if this host has no access to the image registry, "
                    "please pre-load image via `docker load -i <image.tar>` "
                    "or configure `RUNTIME_OPENCLAW_IMAGE_REF` to an internal registry image"
                ),
                500,
            ) from exc

    def ensure_running(self, req: EnsureContainerRequest) -> ContainerStateResponse:
        try:
            logger.info(f"Starting ensure_running for runtime {req.runtimeId}")
            logger.info(f"Config dir: {req.compat.openclawConfigDir}")
            logger.info(f"Workspace dir: {req.compat.openclawWorkspaceDir}")
            
            prepare_runtime_dirs(req.compat.openclawConfigDir, req.compat.openclawWorkspaceDir)
            logger.info("Prepared runtime dirs")

            prepare_skill_dirs(req.userId)
            logger.info("Prepared skill dirs")

            sync_skill_export(req.userId)
            logger.info("Synced skill export")

            # 每次 runtime 启动时同步公共区域快照到用户容器副本目录。
            sync_public_copy_for_user(req.userId)
            logger.info("Synced public-area copy")
            
            write_openclaw_config(req.compat.openclawConfigDir, req.renderedConfig.openclawJson)
            logger.info("Wrote openclaw config")

            def container_ip(c) -> str:
                c.reload()
                return (
                    c.attrs.get("NetworkSettings", {})
                    .get("Networks", {})
                    .get(self._settings.runtime_openclaw_network, {})
                    .get("IPAddress", "")
                )

            # 检查是否存在现有容器
            existing_containers = self._list_managed(req.runtimeId)
            container = None
            
            if existing_containers:
                container = existing_containers[0]
                container.reload()
                logger.info(f"Found existing container: {container.id}, status: {container.status}")
                drifts = detect_drift(container, req, self._settings)
                if drifts:
                    logger.info(f"Detected drift on existing container: {','.join(drifts)}, removing and recreating")
                    container.remove(force=True)
                    container = None
                
                # 如果容器已停止，直接启动它
                if container is not None and container.status in {"exited", "created"}:
                    logger.info("Starting existing stopped container")
                    try:
                        container.start()
                        container.reload()
                    except APIError as exc:
                        logger.error(f"Failed to start existing container: {exc}, recreating")
                        container.remove(force=True)
                        container = None
                        existing_containers = []
                    
                    if container is not None and container.status != "running":
                        logger.error(f"Failed to start existing container, status: {container.status}")
                        container.remove(force=True)
                        container = None
                elif container.status == "running":
                    logger.info("Container is already running")
                    drifts = detect_drift(container, req, self._settings)
                    if drifts:
                        logger.info(f"Drifts detected: {drifts}, recreating container")
                        container.remove(force=True)
                        container = None
                else:
                    # 如果容器处于其他状态（如 restarting, paused, dead），删除并重建
                    if container is not None:
                        logger.info(f"Container in unexpected state: {container.status}, removing and recreating")
                        container.remove(force=True)
                        container = None
            
            # 如果没有现有容器或已删除，则创建新容器
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
                container = self._create_runtime_container(req, labels, alias)
                container.reload()
                logger.info(f"Created container with status: {container.status}")
                
                if container.status != "running":
                    logger.error(f"Container is not running, status: {container.status}")
                    # 清理失败的容器
                    try:
                        container.remove(force=True)
                        logger.info(f"Removed failed container: {container.id}")
                    except Exception as e:
                        logger.error(f"Failed to remove failed container {container.id}: {e}")
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
            
            browser_url = self._browser_url_from_route_host(req.routeHost)
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
                roots = {Path(req.compat.openclawConfigDir), Path(req.compat.openclawWorkspaceDir)}
                dedup: list[Path] = []
                for p in roots:
                    if any(parent in p.parents for parent in dedup):
                        continue
                    dedup = [x for x in dedup if p not in x.parents]
                    dedup.append(p)
                for path in dedup:
                    if path.exists():
                        shutil.rmtree(path)
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
            browserUrl=self._browser_url_from_route_host(self._route_host_from_container(container))
            if observed != "deleted"
            else None,
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
        """
        列出容器内的文件
        """
        try:
            container = self._get_container_by_id(container_id)
            
            # 使用 ls -la 命令列出文件
            cmd = ['ls', '-la', path]
            result = container.exec_run(cmd, user='node')
            
            if result.exit_code != 0:
                raise RuntimeManagerError(
                    "FILE_LIST_FAILED",
                    f"failed to list files: {result.output.decode()}",
                    500,
                )
            
            lines = result.output.decode().split('\n')
            files = []
            
            # 跳过第一行（total ...）和最后一行（空行）
            for line in lines[1:-1]:
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) < 9:
                    continue
                
                permissions = parts[0]
                name = ' '.join(parts[8:])
                size = int(parts[4]) if parts[4].isdigit() else 0
                
                # 判断是否是目录
                is_dir = permissions.startswith('d')
                
                # 跳过 . 和 ..
                if name in ['.', '..']:
                    continue
                
                files.append({
                    'name': name,
                    'path': f'{path}/{name}' if path != '/' else f'/{name}',
                    'type': 'directory' if is_dir else 'file',
                    'size': size,
                })
            
            return files
        except RuntimeManagerError:
            raise
        except Exception as e:
            logger.exception("Failed to list files")
            raise RuntimeManagerError(
                "FILE_LIST_FAILED",
                f"failed to list files: {str(e)}",
                500,
            ) from e

    def read_file(self, container_id: str, path: str) -> str:
        """
        读取容器内的文件内容
        """
        try:
            container = self._get_container_by_id(container_id)
            
            # 使用 cat 命令读取文件
            cmd = ['cat', path]
            result = container.exec_run(cmd, user='node')
            
            if result.exit_code != 0:
                raise RuntimeManagerError(
                    "FILE_READ_FAILED",
                    f"failed to read file: {result.output.decode()}",
                    500,
                )
            
            return result.output.decode()
        except RuntimeManagerError:
            raise
        except Exception as e:
            logger.exception("Failed to read file")
            raise RuntimeManagerError(
                "FILE_READ_FAILED",
                f"failed to read file: {str(e)}",
                500,
            ) from e

    def write_file(self, container_id: str, path: str, content: str) -> None:
        """
        写入文件内容到容器内
        """
        try:
            container = self._get_container_by_id(container_id)
            
            import tempfile
            import os
            import tarfile
            from io import BytesIO
            
            # 获取文件名和目录
            file_dir = os.path.dirname(path)
            file_name = os.path.basename(path)
            
            # 处理二进制内容
            content_bytes = content.encode('utf-8') if isinstance(content, str) else content
            
            # 创建 tar 归档
            tar_buffer = BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                tarinfo = tarfile.TarInfo(name=file_name)
                tarinfo.size = len(content_bytes)
                tarinfo.mtime = int(time.time())
                tarinfo.mode = 0o644
                tar.addfile(tarinfo, BytesIO(content_bytes))
            
            tar_buffer.seek(0)
            
            # 将 tar 归档放入容器
            container.put_archive(file_dir, tar_buffer)
            
            logger.info(f"Successfully wrote file: {path}")
        except RuntimeManagerError:
            raise
        except Exception as e:
            logger.exception("Failed to write file")
            raise RuntimeManagerError(
                "FILE_WRITE_FAILED",
                f"failed to write file: {str(e)}",
                500,
            ) from e
