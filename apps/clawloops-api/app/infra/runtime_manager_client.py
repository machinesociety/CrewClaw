"""
与 runtime-manager 通信的 HTTP 客户端。
"""

from __future__ import annotations

from typing import Any

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

    def list_skills(self, scope: str, user_id: str | None = None) -> list[dict[str, Any]]:
        query = f"/internal/runtime-manager/skills/list?scope={scope}"
        if user_id is not None:
            query += f"&userId={user_id}"
        result = self._request("GET", query)
        files = result.get("files", [])
        return files if isinstance(files, list) else []

    def upload_skill(self, scope: str, content: bytes, filename: str, user_id: str | None = None, name: str | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {"scope": scope}
        if user_id is not None:
            data["userId"] = user_id
        if name is not None:
            data["name"] = name
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
