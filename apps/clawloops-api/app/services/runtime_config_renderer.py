from __future__ import annotations

from app.domain.runtime_ports import ModelConfig
from app.schemas.runtime import RuntimeBindingSnapshot


class RuntimeConfigRenderer:
    """
    负责渲染 RuntimeManager V2.2 所需的完整 openclaw.json。
    """
    def __init__(
        self,
        litellm_api_key: str = "not_empty",
        ollama_base_url: str = "http://ollama:11434",
        ollama_api_key: str = "ollama-local",
    ) -> None:
        self._litellm_api_key = litellm_api_key
        self._ollama_base_url = ollama_base_url.rstrip("/")
        self._ollama_api_key = ollama_api_key

    def render(
        self,
        user_id: str,
        binding: RuntimeBindingSnapshot,
        model_config: ModelConfig,
    ) -> tuple[dict, str]:
        """
        返回 openclaw.json 与 configVersion。
        """
        providers: dict[str, dict] = {}
        rendered_routes: list[str] = []

        for model_id in model_config.models:
            route = model_config.model_routes.get(model_id, f"litellm/{model_id}")
            provider_name, _, provider_model_id = route.partition("/")
            if not provider_name or not provider_model_id:
                provider_name = "litellm"
                provider_model_id = model_id
                route = f"litellm/{model_id}"

            provider_config = providers.get(provider_name)
            if provider_config is None:
                if provider_name == "ollama":
                    provider_config = {
                        "baseUrl": self._ollama_base_url,
                        "apiKey": self._ollama_api_key,
                        "api": "ollama",
                        "models": [],
                    }
                else:
                    provider_config = {
                        "baseUrl": model_config.base_url,
                        "apiKey": self._litellm_api_key,
                        "api": "openai-completions",
                        "models": [],
                    }
                providers[provider_name] = provider_config

            provider_config["models"].append(
                {
                    "id": provider_model_id,
                    "name": (
                        f"{model_id}（免费）"
                        if model_config.model_pricing.get(model_id) == "free"
                        else f"{model_id}（付费）"
                    ),
                    "reasoning": False,
                    "input": ["text"],
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                    "contextWindow": 128000,
                    "maxTokens": 8192,
                }
            )
            rendered_routes.append(route)

        openclaw_json = {
            "auth": {
                "profiles": {
                    "litellm:default": {
                        "provider": "litellm",
                        "mode": "api_key",
                    }
                }
            },
            "gateway": {
                "bind": "lan",
                "port": 18789,
                "mode": "local",
                "controlUi": {
                    "allowedOrigins": ["*"],
                    "dangerouslyAllowHostHeaderOriginFallback": True,
                    "allowInsecureAuth": True,
                    # Keep token-only auth path and disable device pairing prompt.
                    "dangerouslyDisableDeviceAuth": True,
                },
                "auth": {
                    "mode": "token",
                    # V2.2 中 token 由后端渲染结果下发；此处先以可替换引用占位。
                    "token": model_config.gateway_access_token_ref,
                },
            },
            "models": {
                "providers": providers,
                "mode": "replace",
            },
            "agents": {
                "defaults": {
                    "models": {route: {} for route in rendered_routes},
                    "model": {
                        "primary": rendered_routes[0] if rendered_routes else "litellm/default",
                    }
                },
                "list": [{"id": "main", "model": rendered_routes[0]}]
                if rendered_routes
                else [],
            },
        }
        return openclaw_json, model_config.config_render_version
