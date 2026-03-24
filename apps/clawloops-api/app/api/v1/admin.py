from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import (
    get_runtime_service,
    get_user_service,
    require_active_user,
)
from app.core.errors import AccessDeniedError, UserNotFoundError
from app.domain.users import UserStatus
from app.repositories.model_repository import (
    ModelRepository,
    ProviderCredentialRepository,
    UsageRepository,
    get_inmemory_model_repository,
    get_inmemory_provider_credential_repository,
    get_inmemory_usage_repository,
)
from app.schemas.admin import (
    AdminUsageSummaryResponse,
    AdminUserDetailResponse,
    AdminUserListItem,
    AdminUserRuntimeResponse,
    UpdateUserStatusRequest,
)
from app.schemas.credentials import (
    CreateProviderCredentialRequest,
    ProviderCredentialItem,
    ProviderCredentialListResponse,
    VerifyProviderCredentialResponse,
)
from app.schemas.models import AdminModelItem, AdminModelListResponse, UpdateAdminModelRequest
from app.services.model_service import ModelService, ProviderCredentialService, UsageService
from app.services.runtime_service import RuntimeService
from app.services.user_service import UserService


router = APIRouter(tags=["admin"])


def _require_admin(ctx: AuthContext = Depends(require_active_user)) -> AuthContext:
    if not ctx.isAdmin:
        raise AccessDeniedError()
    return ctx


def get_model_service(model_repo: ModelRepository = Depends(get_inmemory_model_repository)) -> ModelService:
    return ModelService(model_repo=model_repo)


def get_provider_credential_service(
    repo: ProviderCredentialRepository = Depends(get_inmemory_provider_credential_repository),
) -> ProviderCredentialService:
    return ProviderCredentialService(credential_repo=repo)


def get_usage_service(repo: UsageRepository = Depends(get_inmemory_usage_repository)) -> UsageService:
    return UsageService(usage_repo=repo)


@router.get("/admin/users", response_model=list[AdminUserListItem])
async def list_users(
    _: AuthContext = Depends(_require_admin),
    user_service: UserService = Depends(get_user_service),
) -> list[AdminUserListItem]:
    repo = user_service._user_repo  # type: ignore[attr-defined]
    users = []
    if hasattr(repo, "_users"):
        users = list(repo._users.values())  # type: ignore[attr-defined]

    return [
        AdminUserListItem(
            userId=u.user_id,
            subjectId=u.subject_id,
            role=u.role.value,
            status=u.status.value,
            runtimeObservedState=(
                user_service.get_runtime_binding(u.user_id).observed_state.value
                if user_service.get_runtime_binding(u.user_id) is not None
                else None
            ),
        )
        for u in users
    ]


@router.get("/admin/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_admin_user_detail(
    user_id: str,
    _: AuthContext = Depends(_require_admin),
    user_service: UserService = Depends(get_user_service),
) -> AdminUserDetailResponse:
    user = user_service.get_user_by_id(user_id)
    if user is None:
        raise UserNotFoundError()

    return AdminUserDetailResponse(
        userId=user.user_id,
        subjectId=user.subject_id,
        tenantId=user.tenant_id,
        role=user.role.value,
        status=user.status.value,
    )


@router.patch("/admin/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    body: UpdateUserStatusRequest,
    _: AuthContext = Depends(_require_admin),
    user_service: UserService = Depends(get_user_service),
    runtime_service: RuntimeService = Depends(get_runtime_service),
) -> dict:
    new_status = UserStatus(body.status)
    user = user_service.set_user_status(user_id, new_status)

    if new_status == UserStatus.DISABLED:
        runtime_service.stop_runtime(user_id)

    return {"userId": user.user_id, "status": user.status.value}


@router.get("/admin/users/{user_id}/runtime", response_model=AdminUserRuntimeResponse)
async def get_admin_user_runtime(
    user_id: str,
    _: AuthContext = Depends(_require_admin),
    user_service: UserService = Depends(get_user_service),
) -> AdminUserRuntimeResponse:
    binding = user_service.get_runtime_binding(user_id)
    if binding is None:
        from app.core.errors import RuntimeNotFoundError

        raise RuntimeNotFoundError()

    return AdminUserRuntimeResponse(
        runtimeId=binding.runtime_id,
        volumeId=binding.volume_id,
        imageRef=binding.image_ref,
        desiredState=binding.desired_state.value,
        observedState=binding.observed_state.value,
        browserUrl=binding.browser_url,
        internalEndpoint=binding.internal_endpoint,
        retentionPolicy=binding.retention_policy.value,
        lastError=binding.last_error,
    )


@router.get("/admin/models", response_model=AdminModelListResponse)
async def list_admin_models(
    _: AuthContext = Depends(_require_admin),
    service: ModelService = Depends(get_model_service),
) -> AdminModelListResponse:
    return AdminModelListResponse(
        models=[
            AdminModelItem(
                modelId=model.model_id,
                name=model.name,
                provider=model.provider,
                source=model.source.value,
                enabled=model.enabled,
                defaultRoute=model.default_route,
                userVisible=model.user_visible,
                defaultProviderCredentialId=model.default_provider_credential_id,
            )
            for model in service.list_models_for_admin()
        ]
    )


@router.put("/admin/models/{model_id}", response_model=AdminModelItem)
async def update_admin_model(
    model_id: str,
    body: UpdateAdminModelRequest,
    _: AuthContext = Depends(_require_admin),
    service: ModelService = Depends(get_model_service),
) -> AdminModelItem:
    model = service.update_model(
        model_id,
        enabled=body.enabled,
        user_visible=body.userVisible,
        default_route=body.defaultRoute,
        default_provider_credential_id=body.defaultProviderCredentialId,
    )
    return AdminModelItem(
        modelId=model.model_id,
        name=model.name,
        provider=model.provider,
        source=model.source.value,
        enabled=model.enabled,
        defaultRoute=model.default_route,
        userVisible=model.user_visible,
        defaultProviderCredentialId=model.default_provider_credential_id,
    )


@router.get("/admin/provider-credentials", response_model=ProviderCredentialListResponse)
async def list_provider_credentials(
    _: AuthContext = Depends(_require_admin),
    service: ProviderCredentialService = Depends(get_provider_credential_service),
) -> ProviderCredentialListResponse:
    return ProviderCredentialListResponse(
        credentials=[
            ProviderCredentialItem(
                credentialId=item.credential_id,
                provider=item.provider,
                name=item.name,
                status=item.status.value,
                verified=item.status.value == "active",
                lastValidatedAt=item.last_validated_at,
            )
            for item in service.list_credentials()
        ]
    )


@router.post("/admin/provider-credentials", response_model=ProviderCredentialItem, status_code=201)
async def create_provider_credential(
    body: CreateProviderCredentialRequest,
    _: AuthContext = Depends(_require_admin),
    service: ProviderCredentialService = Depends(get_provider_credential_service),
) -> ProviderCredentialItem:
    item = service.create_credential(body.provider, body.name, body.secret)
    return ProviderCredentialItem(
        credentialId=item.credential_id,
        provider=item.provider,
        name=item.name,
        status=item.status.value,
        verified=item.status.value == "active",
        lastValidatedAt=item.last_validated_at,
    )


@router.post(
    "/admin/provider-credentials/{credential_id}/verify",
    response_model=VerifyProviderCredentialResponse,
)
async def verify_provider_credential(
    credential_id: str,
    _: AuthContext = Depends(_require_admin),
    service: ProviderCredentialService = Depends(get_provider_credential_service),
) -> VerifyProviderCredentialResponse:
    item = service.verify_credential(credential_id)
    return VerifyProviderCredentialResponse(
        verified=item.status.value == "active",
        status=item.status.value,
        lastValidatedAt=item.last_validated_at,
    )


@router.delete("/admin/provider-credentials/{credential_id}", status_code=204)
async def delete_provider_credential(
    credential_id: str,
    _: AuthContext = Depends(_require_admin),
    service: ProviderCredentialService = Depends(get_provider_credential_service),
) -> None:
    service.delete_credential(credential_id)
    return None


@router.get("/admin/usage/summary", response_model=AdminUsageSummaryResponse)
async def get_admin_usage_summary(
    _: AuthContext = Depends(_require_admin),
    service: UsageService = Depends(get_usage_service),
) -> AdminUsageSummaryResponse:
    summary = service.get_total_usage()
    return AdminUsageSummaryResponse(
        totalTokens=summary.total_tokens,
        usedTokens=summary.used_tokens,
    )


