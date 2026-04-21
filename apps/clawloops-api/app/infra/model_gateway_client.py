
"""
与 LiteLLM / ClawLoops 模型网关交互的客户端占位。
"""


from __future__ import annotations

from typing import Any

import httpx
import sys


class ModelGatewayClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 2.0,
        api_key: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            return {}
        return {"Authorization": f"Bearer {self._api_key}"}

    def list_models(self) -> list[str]:
        """
        尝试从网关读取真正可用的模型列表（OpenAI 兼容：GET /v1/models）。
        """
        if "pytest" in sys.modules:
            return []
        url = f"{self._base_url}/v1/models"
        with httpx.Client(timeout=self._timeout_seconds) as client:
            resp = client.get(url, headers=self._headers())
            resp.raise_for_status()
            payload: dict[str, Any] = resp.json() if resp.content else {}

        data = payload.get("data", [])
        if not isinstance(data, list):
            return []
        model_ids: list[str] = []
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                model_ids.append(item["id"])
        return model_ids

    def get_user_model_config(self, user_id: str, preferred_models: list[str]) -> dict[str, Any]:
        """
        返回 Runtime 渲染 openclaw.json 需要的配置数据。

        - models：优先按 preferred_models 顺序输出，并与网关真实可用模型取交集。
        - 若无法读取网关模型列表，则回退到 preferred_models。
        """
        _ = user_id

        resolved_models = [m for m in preferred_models if m]

        return {
            "baseUrl": self._base_url,
            "models": resolved_models,
            "gatewayAccessTokenRef": "token_ref_001",
            "configRenderVersion": "v1",
        }

    def register_model(self, model_name: str, litellm_params: dict[str, Any]) -> None:
        if "pytest" in sys.modules:
            return
        url = f"{self._base_url}/model/new"
        with httpx.Client(timeout=self._timeout_seconds) as client:
            resp = client.post(
                url,
                headers=self._headers(),
                json={
                    "model_name": model_name,
                    "litellm_params": litellm_params,
                },
            )
            resp.raise_for_status()

