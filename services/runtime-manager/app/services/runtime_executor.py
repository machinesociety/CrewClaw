from __future__ import annotations

import logging
import shutil
import socket
import time
from pathlib import Path

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
from app.services.drift_detector import detect_drift

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuntimeExecutor:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._docker = docker.from_env()

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
        return f"http://{self._settings.runtime_public_host}:{host_port}"

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
        # 先拉取镜像
        try:
            logger.info(f"Pulling image: {self._settings.runtime_openclaw_image_ref}")
            self._docker.images.pull(self._settings.runtime_openclaw_image_ref)
            logger.info("Image pulled successfully")
        except Exception as e:
            logger.error(f"Failed to pull image: {e}")
            raise RuntimeManagerError(
                "RUNTIME_START_FAILED",
                f"failed to pull image: {str(e)}",
                500,
            ) from e
        
        container = self._docker.containers.create(
            image=self._settings.runtime_openclaw_image_ref,
            command=self._settings.runtime_openclaw_command.split(" "),
            labels=labels,
            environment={
                "HOME": "/home/node",
                "TERM": "xterm-256color",
                "TZ": "UTC",
                "OPENAI_BASE_URL": "http://litellm:4000",
            },
            volumes={
                req.compat.openclawConfigDir: {"bind": "/home/node/.openclaw", "mode": "rw"},
                req.compat.openclawWorkspaceDir: {
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
            logger.info(f"Config dir: {req.compat.openclawConfigDir}")
            logger.info(f"Workspace dir: {req.compat.openclawWorkspaceDir}")
            
            prepare_runtime_dirs(req.compat.openclawConfigDir, req.compat.openclawWorkspaceDir)
            logger.info("Prepared runtime dirs")
            
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
                
                # 如果容器已停止，直接启动它
                if container.status in {"exited", "created"}:
                    logger.info("Starting existing stopped container")
                    container.start()
                    container.reload()
                    
                    if container.status != "running":
                        logger.error(f"Failed to start existing container, status: {container.status}")
                        raise RuntimeManagerError("RUNTIME_START_FAILED", "failed to start existing container", 500)
                elif container.status == "running":
                    logger.info("Container is already running")
                else:
                    # 如果容器处于其他状态（如 restarting, paused, dead），删除并重建
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
