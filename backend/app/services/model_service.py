from __future__ import annotations

from datetime import datetime, timezone

from app.core.errors import CredentialNotFoundError
from app.domain.credentials import Credential, CredentialStatus
from app.domain.models import (
    BindingSource,
    Model,
    ModelBinding,
    ModelSource,
    UsageSummary,
)
from app.repositories.model_repository import (
    CredentialRepository,
    ModelBindingRepository,
    ModelRepository,
    UsageRepository,
)


class ModelService:
    """
    模型与绑定相关服务。

    当前实现基于轻量仓储：
    - 模型列表来自 ModelRepository（平台默认模型为主）。
    - 绑定关系存储在 ModelBindingRepository。
    - 凭据元数据来自 CredentialRepository，用于校验归属。
    """

    def __init__(
        self,
        model_repo: ModelRepository,
        binding_repo: ModelBindingRepository,
        credential_repo: CredentialRepository,
    ) -> None:
        self._model_repo = model_repo
        self._binding_repo = binding_repo
        self._credential_repo = credential_repo

    def list_models_for_user(self, user_id: str) -> list[Model]:
        _ = user_id
        return self._model_repo.list_models()

    def list_bindings_for_user(self, user_id: str) -> list[ModelBinding]:
        return self._binding_repo.list_bindings_for_user(user_id)

    def update_binding(
        self,
        user_id: str,
        model_id: str,
        credential_id: str | None,
    ) -> ModelBinding:
        models = {m.model_id: m for m in self._model_repo.list_models()}
        if model_id not in models:
            raise CredentialNotFoundError("Model not found.")

        if credential_id is not None:
            cred = self._credential_repo.get_credential(user_id, credential_id)
            if cred is None:
                raise CredentialNotFoundError()

        binding = ModelBinding(
            user_id=user_id,
            model_id=model_id,
            credential_id=credential_id,
            source=BindingSource.USER_OWNED,
        )
        self._binding_repo.upsert_binding(binding)
        return binding


class CredentialService:
    """
    凭据托管与校验服务。

    当前实现：
    - 仅保存凭据元数据，不持久化明文 secret。
    - verify 时模拟一次成功校验，更新状态与 last_validated_at。
    """

    def __init__(self, credential_repo: CredentialRepository) -> None:
        self._credential_repo = credential_repo

    def list_credentials(self, user_id: str) -> list[Credential]:
        return self._credential_repo.list_credentials_for_user(user_id)

    def create_credential(self, user_id: str, name: str, secret: str) -> Credential:
        _ = secret
        credential = Credential(
            credential_id=f"cred_{abs(hash((user_id, name, secret)))}",
            user_id=user_id,
            name=name,
            status=CredentialStatus.ACTIVE,
            last_validated_at=None,
        )
        self._credential_repo.save(credential)
        return credential

    def verify_credential(self, user_id: str, credential_id: str) -> Credential:
        cred = self._credential_repo.get_credential(user_id, credential_id)
        if cred is None:
            raise CredentialNotFoundError()

        cred.status = CredentialStatus.ACTIVE
        cred.last_validated_at = datetime.now(timezone.utc).isoformat()
        self._credential_repo.save(cred)
        return cred

    def delete_credential(self, user_id: str, credential_id: str) -> None:
        self._credential_repo.delete(user_id, credential_id)


class UsageService:
    """
    用量汇总服务。

    当前实现使用内存仓储聚合用户用量。
    """

    def __init__(self, usage_repo: UsageRepository) -> None:
        self._usage_repo = usage_repo

    def get_user_usage(self, user_id: str) -> UsageSummary:
        return self._usage_repo.get_user_usage(user_id)

