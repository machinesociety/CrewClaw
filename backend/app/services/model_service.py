from __future__ import annotations

from datetime import datetime, timezone

from app.core.errors import (
    ModelNotFoundError,
    ProviderCredentialInvalidError,
    ProviderCredentialNotFoundError,
)
from app.domain.credentials import ProviderCredential, ProviderCredentialStatus
from app.domain.models import Model, UsageSummary
from app.repositories.model_repository import (
    ModelRepository,
    ProviderCredentialRepository,
    UsageRepository,
)


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

    def list_models_for_admin(self) -> list[Model]:
        return self._model_repo.list_models()

    def update_model(
        self,
        model_id: str,
        *,
        enabled: bool | None = None,
        user_visible: bool | None = None,
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
        if default_route is not None:
            model.default_route = default_route
        if default_provider_credential_id is not None:
            model.default_provider_credential_id = default_provider_credential_id

        self._model_repo.save(model)
        return model


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

