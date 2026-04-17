from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session

from app.domain.credentials import ProviderCredential, ProviderCredentialStatus
from app.domain.models import Model, ModelSource, PricingType, UsageSummary
from app.models.model_catalog import GovernedModelCatalogModel


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
            model.model_id: model for model in build_default_governed_models()
        }

    def list_models(self) -> list[Model]:
        return list(self._models.values())

    def get_model(self, model_id: str) -> Model | None:
        return self._models.get(model_id)

    def save(self, model: Model) -> None:
        self._models[model.model_id] = model


def build_default_governed_models() -> list[Model]:
    return [
        Model(
            model_id="ollama-qwen2.5-7b-free",
            name="Qwen 2.5 7B（免费）",
            provider="ollama",
            source=ModelSource.SHARED,
            pricing_type=PricingType.FREE,
            enabled=True,
            user_visible=True,
            default_route="ollama/qwen2.5:7b",
            default_provider_credential_id=None,
            upstream_model_id="qwen2.5:7b",
        ),
        Model(
            model_id="qwen-max-proxy",
            name="通义 Qwen Max（免费）",
            provider="dashscope",
            source=ModelSource.SHARED,
            pricing_type=PricingType.FREE,
            enabled=True,
            user_visible=True,
            default_route="litellm/qwen-max-proxy",
            default_provider_credential_id=None,
            upstream_model_id="dashscope/qwen3.5-plus",
        ),
        Model(
            model_id="gpt-4-mini-paid",
            name="GPT-4 Mini",
            provider="openrouter",
            source=ModelSource.SHARED,
            pricing_type=PricingType.PAID,
            enabled=True,
            user_visible=True,
            default_route="openrouter/openai/gpt-4o-mini",
            default_provider_credential_id=None,
            upstream_model_id="openai/gpt-4o-mini",
        ),
    ]


class SqlAlchemyModelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._ensure_seed_data()

    def _ensure_seed_data(self) -> None:
        existing_count = self._session.query(GovernedModelCatalogModel).count()
        if existing_count > 0:
            return
        for model in build_default_governed_models():
            self._session.add(self._to_row(model))
        self._session.commit()

    def list_models(self) -> list[Model]:
        rows = (
            self._session.query(GovernedModelCatalogModel)
            .order_by(GovernedModelCatalogModel.id.asc())
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def get_model(self, model_id: str) -> Model | None:
        row = (
            self._session.query(GovernedModelCatalogModel)
            .filter(GovernedModelCatalogModel.model_id == model_id)
            .one_or_none()
        )
        return None if row is None else self._to_domain(row)

    def save(self, model: Model) -> None:
        row = (
            self._session.query(GovernedModelCatalogModel)
            .filter(GovernedModelCatalogModel.model_id == model.model_id)
            .one_or_none()
        )
        if row is None:
            row = self._to_row(model)
            self._session.add(row)
        else:
            row.name = model.name
            row.provider = model.provider
            row.source = model.source
            row.pricing_type = model.pricing_type
            row.enabled = model.enabled
            row.user_visible = model.user_visible
            row.default_route = model.default_route
            row.default_provider_credential_id = model.default_provider_credential_id
            row.upstream_model_id = model.upstream_model_id
        self._session.commit()

    @staticmethod
    def _to_domain(row: GovernedModelCatalogModel) -> Model:
        return Model(
            model_id=row.model_id,
            name=row.name,
            provider=row.provider,
            source=row.source,
            pricing_type=row.pricing_type,
            enabled=row.enabled,
            user_visible=row.user_visible,
            default_route=row.default_route,
            default_provider_credential_id=row.default_provider_credential_id,
            upstream_model_id=row.upstream_model_id,
        )

    @staticmethod
    def _to_row(model: Model) -> GovernedModelCatalogModel:
        return GovernedModelCatalogModel(
            model_id=model.model_id,
            name=model.name,
            provider=model.provider,
            source=model.source,
            pricing_type=model.pricing_type,
            enabled=model.enabled,
            user_visible=model.user_visible,
            default_route=model.default_route,
            default_provider_credential_id=model.default_provider_credential_id,
            upstream_model_id=model.upstream_model_id,
        )


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
