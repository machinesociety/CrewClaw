"""
与 runtime-manager 通信的 HTTP 客户端。
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx


class RuntimeManagerClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        # RM ensure-running can block until readiness window completes.
        self._timeout = httpx.Timeout(45.0, connect=5.0)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
            response = client.request(method, path, json=payload)
        if response.is_error:
            detail = None
            try:
                body = response.json()
                if isinstance(body, dict):
                    detail_obj = body.get("detail")
                    if isinstance(detail_obj, dict):
                        detail = f"{detail_obj.get('code', 'RM_ERROR')}: {detail_obj.get('message', response.text)}"
            except Exception:
                detail = None
            raise RuntimeError(detail or f"runtime-manager request failed: {response.status_code}")
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("runtime-manager response is not a JSON object")
        return data

    def _request_bytes(self, method: str, path: str) -> tuple[bytes, dict[str, str]]:
        with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
            response = client.request(method, path)
        if response.is_error:
            raise RuntimeError(f"runtime-manager request failed: {response.status_code}")
        return response.content, {k: v for k, v in response.headers.items()}

    def _request_multipart(
        self,
        path: str,
        data: dict[str, Any],
        files: dict[str, tuple[str, bytes, str]],
    ) -> dict[str, Any]:
        with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
            response = client.post(path, data=data, files=files)
        if response.is_error:
            raise RuntimeError(f"runtime-manager request failed: {response.status_code}")
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("runtime-manager response is not a JSON object")
        return body

    def _request_form(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
            response = client.post(path, data=data)
        if response.is_error:
            raise RuntimeError(f"runtime-manager request failed: {response.status_code}")
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("runtime-manager response is not a JSON object")
        return body

    def ensure_running(self, payload: dict) -> dict:
        return self._request("POST", "/internal/runtime-manager/containers/ensure-running", payload)

    def stop(self, user_id: str, runtime_id: str) -> Any:
        return self._request(
            "POST",
            "/internal/runtime-manager/containers/stop",
            {"userId": user_id, "runtimeId": runtime_id},
        )

    def delete(
        self,
        user_id: str,
        runtime_id: str,
        retention_policy: str,
        compat: dict[str, str] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "userId": user_id,
            "runtimeId": runtime_id,
            "retentionPolicy": retention_policy,
        }
        if compat is not None:
            payload["compat"] = compat
        return self._request(
            "POST",
            "/internal/runtime-manager/containers/delete",
            payload,
        )

    def restart(self, runtime_id: str) -> Any:
        return self._request(
            "POST",
            "/internal/runtime-manager/containers/restart",
            {"runtimeId": runtime_id},
        )

    def get_container(self, runtime_id: str) -> dict[str, Any]:
        return self._request("GET", f"/internal/runtime-manager/containers/{runtime_id}")

    def list_files(self, runtime_id: str, path: str) -> list[dict]:
        response_data = self._request("GET", f"/internal/runtime-manager/files/list?runtimeId={runtime_id}&path={path}")
        # 确保返回的是一个列表
        if isinstance(response_data, dict) and 'files' in response_data:
            return response_data['files']
        return []

    def read_file(self, runtime_id: str, path: str) -> str:
        result = self._request("GET", f"/internal/runtime-manager/files/read?runtimeId={runtime_id}&path={path}")
        return result.get("content", "")

    def write_file(self, runtime_id: str, path: str, content: str | bytes) -> None:
        # 如果是二进制内容，转换为base64编码
        import base64
        if isinstance(content, bytes):
            content = base64.b64encode(content).decode('utf-8')
            is_binary = True
        else:
            is_binary = False
        
        self._request("PUT", "/internal/runtime-manager/files/write", {
            "runtimeId": runtime_id,
            "path": path,
            "content": content,
            "isBinary": is_binary
        })

    def write_runtime_openclaw_config(self, runtime_id: str, openclaw_json: dict[str, Any]) -> None:
        import json

        payload = json.dumps(openclaw_json, ensure_ascii=False, indent=2)
        self.write_file(runtime_id=runtime_id, path="/home/node/.openclaw/openclaw.json", content=payload)

    def list_skills(self, scope: str, user_id: str | None = None) -> list[dict[str, Any]]:
        query = f"/internal/runtime-manager/skills/list?scope={scope}"
        if user_id is not None:
            query += f"&userId={user_id}"
        result = self._request("GET", query)
        files = result.get("files", [])
        return files if isinstance(files, list) else []

    def upload_skill(
        self,
        scope: str,
        content: bytes,
        filename: str,
        user_id: str | None = None,
        name: str | None = None,
        overwrite: bool | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {"scope": scope}
        if user_id is not None:
            data["userId"] = user_id
        if name is not None:
            data["name"] = name
        if overwrite is not None:
            data["overwrite"] = str(bool(overwrite)).lower()
        return self._request_multipart(
            "/internal/runtime-manager/skills/upload",
            data=data,
            files={"file": (filename, content, "application/octet-stream")},
        )

    def download_skill(self, scope: str, name: str, user_id: str | None = None) -> tuple[bytes, dict[str, str]]:
        query = f"/internal/runtime-manager/skills/download?scope={scope}&name={name}"
        if user_id is not None:
            query += f"&userId={user_id}"
        return self._request_bytes("GET", query)

    def delete_skill(self, scope: str, name: str, user_id: str | None = None) -> None:
        query = f"/internal/runtime-manager/skills/delete?scope={scope}&name={name}"
        if user_id is not None:
            query += f"&userId={user_id}"
        self._request("DELETE", query)

    def list_public_entries(
        self,
        path: str = "",
        page: int = 1,
        page_size: int = 10,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        query = f"/internal/runtime-manager/public/files/list?page={page}&pageSize={page_size}"
        if path:
            query += f"&path={quote(path, safe='')}"
        if user_id:
            query += f"&userId={quote(user_id, safe='')}"
        return self._request("GET", query)

    def upload_public_file(
        self,
        path: str,
        content: bytes,
        filename: str,
        overwrite: bool,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {"path": path, "overwrite": str(bool(overwrite)).lower()}
        if user_id:
            data["userId"] = user_id
        return self._request_multipart(
            "/internal/runtime-manager/public/files/upload",
            data=data,
            files={"file": (filename, content, "application/octet-stream")},
        )

    def download_public_file(self, path: str, user_id: str | None = None) -> tuple[bytes, dict[str, str]]:
        query = f"/internal/runtime-manager/public/files/download?path={quote(path, safe='')}"
        if user_id:
            query += f"&userId={quote(user_id, safe='')}"
        return self._request_bytes("GET", query)

    def delete_public_path(self, path: str, user_id: str | None = None) -> None:
        query = f"/internal/runtime-manager/public/files/delete?path={quote(path, safe='')}"
        if user_id:
            query += f"&userId={quote(user_id, safe='')}"
        self._request("DELETE", query)

    def mkdir_public_dir(self, path: str, user_id: str | None = None) -> None:
        data: dict[str, Any] = {"path": path}
        if user_id:
            data["userId"] = user_id
        self._request_form("/internal/runtime-manager/public/files/mkdir", data=data)
