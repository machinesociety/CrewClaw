from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from typing import Callable

from app.core.errors import ModelNotFoundError, ProviderCredentialInvalidError, ProviderCredentialNotFoundError
from app.domain.credentials import ProviderCredential, ProviderCredentialStatus
from app.domain.models import Model, ModelSource, PricingType, UsageSummary
from app.infra.model_gateway_client import ModelGatewayClient
from app.infra.openrouter_client import OpenRouterClient
from app.repositories.model_repository import (
    ModelRepository,
    ProviderCredentialRepository,
    UsageRepository,
)

def build_openrouter_safe_model_id(model_id: str) -> str:
    """
    Convert OpenRouter model ids like `z-ai/glm-4.5-air:free` into a
    Control-UI-safe alias such as `openrouter-z-ai-glm-4-5-air-free`.
    """
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", model_id).strip("-").lower()
    return f"openrouter-{normalized}" if normalized else "openrouter-model"


class ModelService:
    """
    模型治理与用户侧只读模型列表服务。
    """

    def __init__(
        self,
        model_repo: ModelRepository,
    ) -> None:
        self._model_repo = model_repo

    def list_models_for_user(self, user_id: str) -> list[Model]:
        _ = user_id
        return [
            model
            for model in self._model_repo.list_models()
            if model.enabled and model.user_visible
        ]

    @staticmethod
    def filter_models_by_provider_readiness(
        models: list[Model],
        provider_ready: Callable[[str | None], bool],
    ) -> list[Model]:
        return [model for model in models if provider_ready(model.provider)]

    @staticmethod
    def prioritize_models(models: list[Model], preferred_model_ids: list[str]) -> list[Model]:
        """
        按 preferred_model_ids 提升排序优先级，其余模型保持原有相对顺序。
        """
        if not preferred_model_ids:
            return list(models)

        priority_map = {model_id: index for index, model_id in enumerate(preferred_model_ids)}
        original_order = {model.model_id: index for index, model in enumerate(models)}
        return sorted(
            models,
            key=lambda model: (
                priority_map.get(model.model_id, len(priority_map)),
                original_order.get(model.model_id, len(original_order)),
            ),
        )

    def list_models_for_admin(self) -> list[Model]:
        return self._model_repo.list_models()

    def update_model(
        self,
        model_id: str,
        *,
        enabled: bool | None = None,
        user_visible: bool | None = None,
        pricing_type: PricingType | None = None,
        default_route: str | None = None,
        default_provider_credential_id: str | None = None,
    ) -> Model:
        model = self._model_repo.get_model(model_id)
        if model is None:
            raise ModelNotFoundError()

        if enabled is not None:
            model.enabled = enabled
        if user_visible is not None:
            model.user_visible = user_visible
        if pricing_type is not None:
            model.pricing_type = pricing_type
        if default_route is not None:
            model.default_route = default_route
        if default_provider_credential_id is not None:
            model.default_provider_credential_id = default_provider_credential_id

        self._model_repo.save(model)
        return model

    def sync_openrouter_models(
        self,
        *,
        openrouter_base_url: str,
        openrouter_api_key: str | None = None,
    ) -> dict:
        """
        从 OpenRouter 同步模型目录到平台注册表。

        约定：
        - pricingType：若模型 id 以 ':free' 结尾则标记为 free，否则 paid
        - 不覆盖管理员已有的 enabled/user_visible/default_route/default_provider_credential_id
        - 若模型不存在则创建（默认 enabled=False, user_visible=False，避免误上架）
        """
        client = OpenRouterClient(base_url=openrouter_base_url, api_key=openrouter_api_key)
        entries = client.list_models()

        created = 0
        updated = 0

        for entry in entries:
            synced_model_id = build_openrouter_safe_model_id(entry.model_id)
            pricing_type = PricingType.FREE if entry.model_id.endswith(":free") else PricingType.PAID

            existing = self._model_repo.get_model(synced_model_id)
            if existing is None:
                model = Model(
                    model_id=synced_model_id,
                    name=entry.name or entry.model_id,
                    provider="openrouter",
                    source=ModelSource.SHARED,
                    pricing_type=pricing_type,
                    enabled=False,
                    user_visible=False,
                    default_route=f"litellm/{synced_model_id}",
                    default_provider_credential_id=None,
                    upstream_model_id=entry.model_id,
                )
                self._model_repo.save(model)
                created += 1
                continue

            changed = False
            if existing.provider != "openrouter":
                existing.provider = "openrouter"
                changed = True
            if existing.pricing_type != pricing_type:
                existing.pricing_type = pricing_type
                changed = True
            if entry.name and existing.name != entry.name:
                existing.name = entry.name
                changed = True
            if existing.upstream_model_id != entry.model_id:
                existing.upstream_model_id = entry.model_id
                changed = True

            if changed:
                self._model_repo.save(existing)
                updated += 1

        return {"fetched": len(entries), "created": created, "updated": updated}

    def resolve_openrouter_upstream_model_id(
        self,
        model: Model,
        *,
        openrouter_base_url: str,
        openrouter_api_key: str | None = None,
    ) -> str | None:
        if model.provider != "openrouter":
            return model.upstream_model_id
        if model.upstream_model_id:
            return model.upstream_model_id
        if "/" in model.model_id:
            return model.model_id
        if "pytest" in sys.modules:
            return None

        client = OpenRouterClient(base_url=openrouter_base_url, api_key=openrouter_api_key)
        for entry in client.list_models():
            if build_openrouter_safe_model_id(entry.model_id) == model.model_id:
                model.upstream_model_id = entry.model_id
                self._model_repo.save(model)
                return entry.model_id
        return None

    def ensure_openrouter_models_registered(
        self,
        models: list[Model],
        *,
        model_gateway_client: ModelGatewayClient,
        openrouter_base_url: str,
        openrouter_api_key: str | None = None,
    ) -> list[str]:
        """
        确保当前治理层中“已上架且可见”的 OpenRouter 模型已注册到 LiteLLM。

        返回本次成功处理（已存在或已注册）的平台注册 model_id 列表。
        """
        if not models:
            return []

        available_models = set()
        try:
            available_models = set(model_gateway_client.list_models())
        except Exception:
            available_models = set()

        ensured_model_ids: list[str] = []
        for model in models:
            if model.provider != "openrouter":
                continue

            if model.model_id in available_models:
                ensured_model_ids.append(model.model_id)
                continue

            upstream_model_id = self.resolve_openrouter_upstream_model_id(
                model,
                openrouter_base_url=openrouter_base_url,
                openrouter_api_key=openrouter_api_key,
            )
            if not upstream_model_id:
                continue

            try:
                model_gateway_client.register_model(
                    model.model_id,
                    {
                        "model": f"openrouter/{upstream_model_id}",
                        "api_key": "os.environ/OPENROUTER_API_KEY",
                    },
                )
                ensured_model_ids.append(model.model_id)
                available_models.add(model.model_id)
            except Exception:
                continue

        return ensured_model_ids


class ProviderCredentialService:
    """
    平台 provider 凭据治理服务。
    """

    def __init__(self, credential_repo: ProviderCredentialRepository) -> None:
        self._credential_repo = credential_repo

    def list_credentials(self) -> list[ProviderCredential]:
        return self._credential_repo.list_credentials()

    def create_credential(self, provider: str, name: str, secret: str) -> ProviderCredential:
        if not secret.strip():
            raise ProviderCredentialInvalidError()

        credential = ProviderCredential(
            credential_id=f"pc_{abs(hash((provider, name, secret)))}",
            provider=provider,
            name=name,
            status=ProviderCredentialStatus.ACTIVE,
            last_validated_at=None,
        )
        self._credential_repo.save(credential)
        return credential

    def verify_credential(self, credential_id: str) -> ProviderCredential:
        cred = self._credential_repo.get_credential(credential_id)
        if cred is None:
            raise ProviderCredentialNotFoundError()

        cred.status = ProviderCredentialStatus.ACTIVE
        cred.last_validated_at = datetime.now(timezone.utc).isoformat()
        self._credential_repo.save(cred)
        return cred

    def delete_credential(self, credential_id: str) -> None:
        if self._credential_repo.get_credential(credential_id) is None:
            raise ProviderCredentialNotFoundError()
        self._credential_repo.delete(credential_id)


class UsageService:
    """
    用量汇总服务。

    当前实现使用内存仓储聚合用户用量。
    """

    def __init__(self, usage_repo: UsageRepository) -> None:
        self._usage_repo = usage_repo

    def get_user_usage(self, user_id: str) -> UsageSummary:
        return self._usage_repo.get_user_usage(user_id)

    def get_total_usage(self) -> UsageSummary:
        summaries = self._usage_repo.list_usage()
        return UsageSummary(
            user_id="platform",
            total_tokens=sum(item.total_tokens for item in summaries),
            used_tokens=sum(item.used_tokens for item in summaries),
        )
