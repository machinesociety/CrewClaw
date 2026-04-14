from __future__ import annotations

from typing import Protocol

from app.domain.credentials import ProviderCredential, ProviderCredentialStatus
from app.domain.models import Model, ModelSource, PricingType, UsageSummary


class ModelRepository(Protocol):
    def list_models(self) -> list[Model]:
        ...

    def get_model(self, model_id: str) -> Model | None:
        ...

    def save(self, model: Model) -> None:
        ...


class ProviderCredentialRepository(Protocol):
    def list_credentials(self) -> list[ProviderCredential]:
        ...

    def get_credential(self, credential_id: str) -> ProviderCredential | None:
        ...

    def save(self, credential: ProviderCredential) -> None:
        ...

    def delete(self, credential_id: str) -> None:
        ...


class UsageRepository(Protocol):
    def get_user_usage(self, user_id: str) -> UsageSummary:
        ...

    def set_user_usage(self, summary: UsageSummary) -> None:
        ...

    def list_usage(self) -> list[UsageSummary]:
        ...


class InMemoryModelRepository:
    def __init__(self) -> None:
        # model_id 必须与 LiteLLM model_list.model_name 一致，便于与网关 /v1/models 取交集。
        self._models: dict[str, Model] = {
            "qwen-max-proxy": Model(
                model_id="qwen-max-proxy",
                name="通义 Qwen Max（免费）",
                provider="dashscope",
                source=ModelSource.SHARED,
                pricing_type=PricingType.FREE,
                enabled=True,
                user_visible=True,
                default_route="litellm/qwen-max-proxy",
                default_provider_credential_id=None,
            ),
            "gpt-4-mini-paid": Model(
                model_id="gpt-4-mini-paid",
                name="GPT-4 Mini",
                provider="openrouter",
                source=ModelSource.SHARED,
                pricing_type=PricingType.PAID,
                enabled=True,
                user_visible=True,
                default_route="openrouter/openai/gpt-4o-mini",
                default_provider_credential_id=None,
            ),
        }

    def list_models(self) -> list[Model]:
        return list(self._models.values())

    def get_model(self, model_id: str) -> Model | None:
        return self._models.get(model_id)

    def save(self, model: Model) -> None:
        self._models[model.model_id] = model


class InMemoryProviderCredentialRepository:
    def __init__(self) -> None:
        self._credentials: dict[str, ProviderCredential] = {}

    def list_credentials(self) -> list[ProviderCredential]:
        return list(self._credentials.values())

    def get_credential(self, credential_id: str) -> ProviderCredential | None:
        return self._credentials.get(credential_id)

    def save(self, credential: ProviderCredential) -> None:
        self._credentials[credential.credential_id] = credential

    def delete(self, credential_id: str) -> None:
        self._credentials.pop(credential_id, None)


class InMemoryUsageRepository:
    def __init__(self) -> None:
        self._usage: dict[str, UsageSummary] = {}

    def get_user_usage(self, user_id: str) -> UsageSummary:
        summary = self._usage.get(user_id)
        if summary is None:
            summary = UsageSummary(user_id=user_id, total_tokens=0, used_tokens=0)
            self._usage[user_id] = summary
        return summary

    def set_user_usage(self, summary: UsageSummary) -> None:
        self._usage[summary.user_id] = summary

    def list_usage(self) -> list[UsageSummary]:
        return list(self._usage.values())


_model_repo_singleton: InMemoryModelRepository | None = None
_provider_credential_repo_singleton: InMemoryProviderCredentialRepository | None = None
_usage_repo_singleton: InMemoryUsageRepository | None = None


def get_inmemory_model_repository() -> InMemoryModelRepository:
    global _model_repo_singleton
    if _model_repo_singleton is None:
        _model_repo_singleton = InMemoryModelRepository()
    return _model_repo_singleton


def get_inmemory_provider_credential_repository() -> InMemoryProviderCredentialRepository:
    global _provider_credential_repo_singleton
    if _provider_credential_repo_singleton is None:
        _provider_credential_repo_singleton = InMemoryProviderCredentialRepository()
    return _provider_credential_repo_singleton


def get_inmemory_usage_repository() -> InMemoryUsageRepository:
    global _usage_repo_singleton
    if _usage_repo_singleton is None:
        _usage_repo_singleton = InMemoryUsageRepository()
    return _usage_repo_singleton


def reset_inmemory_model_repositories() -> None:
    global _model_repo_singleton, _provider_credential_repo_singleton, _usage_repo_singleton
    _model_repo_singleton = None
    _provider_credential_repo_singleton = None
    _usage_repo_singleton = None

