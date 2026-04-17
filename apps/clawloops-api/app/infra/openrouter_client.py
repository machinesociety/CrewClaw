from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class OpenRouterModelEntry:
    model_id: str
    name: str | None = None


class OpenRouterClient:
    def __init__(self, base_url: str, api_key: str | None = None, timeout_seconds: float = 6.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def list_models(self) -> list[OpenRouterModelEntry]:
        url = f"{self._base_url}/models"
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        with httpx.Client(timeout=self._timeout_seconds) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            payload: dict[str, Any] = resp.json() if resp.content else {}

        data = payload.get("data", [])
        if not isinstance(data, list):
            return []

        out: list[OpenRouterModelEntry] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if not isinstance(model_id, str) or not model_id.strip():
                continue
            name = item.get("name")
            out.append(OpenRouterModelEntry(model_id=model_id, name=name if isinstance(name, str) else None))
        return out
