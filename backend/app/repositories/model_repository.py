from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol

from app.domain.credentials import Credential, CredentialStatus
from app.domain.models import BindingSource, Model, ModelBinding, ModelSource, UsageSummary


class ModelRepository(Protocol):
    """
    模型元数据仓储接口。

    当前仅提供读取能力，MVP 阶段使用内置静态配置。
    """

    def list_models(self) -> list[Model]:
        ...


class ModelBindingRepository(Protocol):
    """
    模型与凭据绑定关系仓储接口。
    """

    def list_bindings_for_user(self, user_id: str) -> list[ModelBinding]:
        ...

    def get_binding(self, user_id: str, model_id: str) -> ModelBinding | None:
        ...

    def upsert_binding(self, binding: ModelBinding) -> None:
        ...

    def delete_binding(self, user_id: str, model_id: str) -> None:
        ...


class CredentialRepository(Protocol):
    """
    用户凭据元数据仓储接口（不包含明文 secret）。
    """

    def list_credentials_for_user(self, user_id: str) -> list[Credential]:
        ...

    def get_credential(self, user_id: str, credential_id: str) -> Credential | None:
        ...

    def save(self, credential: Credential) -> None:
        ...

    def delete(self, user_id: str, credential_id: str) -> None:
        ...


class UsageRepository(Protocol):
    """
    用量汇总仓储接口。
    """

    def get_user_usage(self, user_id: str) -> UsageSummary:
        ...

    def set_user_usage(self, summary: UsageSummary) -> None:
        ...


class InMemoryModelRepository:
    """
    内存版模型仓储，提供平台默认模型列表。
    """

    def __init__(self) -> None:
        self._models: list[Model] = [
            Model(
                model_id="gpt-4-mini",
                name="GPT-4 Mini",
                provider="openai",
                source=ModelSource.SHARED,
                enabled=True,
            )
        ]

    def list_models(self) -> list[Model]:
        return list(self._models)


class InMemoryModelBindingRepository:
    """
    内存版模型绑定仓储。
    """

    def __init__(self) -> None:
        # key: (user_id, model_id)
        self._bindings: Dict[tuple[str, str], ModelBinding] = {}

    def list_bindings_for_user(self, user_id: str) -> list[ModelBinding]:
        return [b for (uid, _), b in self._bindings.items() if uid == user_id]

    def get_binding(self, user_id: str, model_id: str) -> ModelBinding | None:
        return self._bindings.get((user_id, model_id))

    def upsert_binding(self, binding: ModelBinding) -> None:
        key = (binding.user_id, binding.model_id)
        self._bindings[key] = binding

    def delete_binding(self, user_id: str, model_id: str) -> None:
        self._bindings.pop((user_id, model_id), None)


class InMemoryCredentialRepository:
    """
    内存版凭据仓储。

    仅保存凭据元数据，secret 由其它组件或测试代码管理。
    """

    def __init__(self) -> None:
        self._credentials: Dict[tuple[str, str], Credential] = {}

    def list_credentials_for_user(self, user_id: str) -> list[Credential]:
        return [c for (uid, _), c in self._credentials.items() if uid == user_id]

    def get_credential(self, user_id: str, credential_id: str) -> Credential | None:
        return self._credentials.get((user_id, credential_id))

    def save(self, credential: Credential) -> None:
        key = (credential.user_id, credential.credential_id)
        self._credentials[key] = credential

    def delete(self, user_id: str, credential_id: str) -> None:
        self._credentials.pop((user_id, credential_id), None)


class InMemoryUsageRepository:
    """
    内存版用量汇总仓储。
    """

    def __init__(self) -> None:
        self._usage: Dict[str, UsageSummary] = {}

    def get_user_usage(self, user_id: str) -> UsageSummary:
        summary = self._usage.get(user_id)
        if summary is None:
            summary = UsageSummary(user_id=user_id, total_tokens=0)
            self._usage[user_id] = summary
        return summary

    def set_user_usage(self, summary: UsageSummary) -> None:
        self._usage[summary.user_id] = summary


# 单例实例，供 API 层在同一进程内共享状态，便于集成测试。
_model_repo_singleton: InMemoryModelRepository | None = None
_binding_repo_singleton: InMemoryModelBindingRepository | None = None
_credential_repo_singleton: InMemoryCredentialRepository | None = None
_usage_repo_singleton: InMemoryUsageRepository | None = None


def get_inmemory_model_repository() -> InMemoryModelRepository:
    global _model_repo_singleton
    if _model_repo_singleton is None:
        _model_repo_singleton = InMemoryModelRepository()
    return _model_repo_singleton


def get_inmemory_model_binding_repository() -> InMemoryModelBindingRepository:
    global _binding_repo_singleton
    if _binding_repo_singleton is None:
        _binding_repo_singleton = InMemoryModelBindingRepository()
    return _binding_repo_singleton


def get_inmemory_credential_repository() -> InMemoryCredentialRepository:
    global _credential_repo_singleton
    if _credential_repo_singleton is None:
        _credential_repo_singleton = InMemoryCredentialRepository()
    return _credential_repo_singleton


def get_inmemory_usage_repository() -> InMemoryUsageRepository:
    global _usage_repo_singleton
    if _usage_repo_singleton is None:
        _usage_repo_singleton = InMemoryUsageRepository()
    return _usage_repo_singleton


