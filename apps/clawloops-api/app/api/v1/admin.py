from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import AuthContext
from app.core.dependencies import (
    get_db_session_dep,
    get_invitation_service,
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
from app.schemas.invitations import AdminInvitationItem, AdminInvitationListResponse, CreateAdminInvitationRequest
from app.schemas.admin_home import (
    AdminHomeAttention,
    AdminHomeResponse,
    AdminHomeRuntimeAlert,
    AdminHomeSummary,
)
from app.schemas.credentials import (
    CreateProviderCredentialRequest,
    ProviderCredentialItem,
    ProviderCredentialListResponse,
    VerifyProviderCredentialResponse,
)
from app.schemas.models import AdminModelItem, AdminModelListResponse, UpdateAdminModelRequest
from app.services.invitation_service import InvitationService
from app.services.model_service import ModelService, ProviderCredentialService, UsageService
from app.services.runtime_service import RuntimeService
from app.services.user_service import UserService


router = APIRouter(tags=["admin"])


def _require_admin(ctx: AuthContext = Depends(require_active_user)) -> AuthContext:
    if not ctx.isAdmin:
        raise AccessDeniedError()
    return ctx


def _to_admin_inv(inv) -> AdminInvitationItem:
    return AdminInvitationItem(
        invitationId=inv.invitation_id,
        targetEmail=inv.target_email,
        loginUsername=inv.login_username,
        workspaceId=inv.workspace_id,
        role=inv.role,
        status=inv.status.value,
        expiresAt=inv.expires_at,
        consumedAt=inv.consumed_at,
        consumedByUserId=inv.consumed_by_user_id,
        lastError=inv.last_error,
        createdAt=inv.created_at,
    )


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


@router.get("/admin/invitations", response_model=AdminInvitationListResponse)
async def list_admin_invitations(
    _: AuthContext = Depends(_require_admin),
    svc: InvitationService = Depends(get_invitation_service),
) -> AdminInvitationListResponse:
    return AdminInvitationListResponse(invitations=[_to_admin_inv(i) for i in svc.list_invitations()])


@router.post("/admin/invitations", response_model=AdminInvitationItem, status_code=201)
async def create_admin_invitation(
    body: CreateAdminInvitationRequest,
    ctx: AuthContext = Depends(_require_admin),
    svc: InvitationService = Depends(get_invitation_service),
) -> AdminInvitationItem:
    inv = svc.create_admin_invitation(
        target_email=body.targetEmail,
        login_username=body.loginUsername,
        workspace_id=body.workspaceId,
        role=body.role,
        expires_in_hours=body.expiresInHours,
        created_by_user_id=ctx.userId,
    )
    return _to_admin_inv(inv)


@router.get("/admin/invitations/{invitation_id}", response_model=AdminInvitationItem)
async def get_admin_invitation(
    invitation_id: str,
    _: AuthContext = Depends(_require_admin),
    svc: InvitationService = Depends(get_invitation_service),
) -> AdminInvitationItem:
    return _to_admin_inv(svc.get_admin_invitation(invitation_id))


@router.post("/admin/invitations/{invitation_id}/revoke")
async def revoke_admin_invitation(
    invitation_id: str,
    _: AuthContext = Depends(_require_admin),
    svc: InvitationService = Depends(get_invitation_service),
) -> dict:
    svc.revoke(invitation_id)
    return {"status": "ok"}


@router.post("/admin/invitations/{invitation_id}/resend")
async def resend_admin_invitation(
    invitation_id: str,
    _: AuthContext = Depends(_require_admin),
    svc: InvitationService = Depends(get_invitation_service),
) -> dict:
    # MVP: 仅占位（真实邮件发送由后续模块承接）
    _ = svc.get_admin_invitation(invitation_id)
    return {"status": "ok"}


@router.get("/admin/home", response_model=AdminHomeResponse)
async def get_admin_home(
    _: AuthContext = Depends(_require_admin),
    db: Session = Depends(get_db_session_dep),
) -> AdminHomeResponse:
    """
    v0.11：管理后台首页摘要聚合接口。

    MVP：直接从 SQLite 真相表聚合最小字段。
    """
    from app.domain.invitations import InvitationStatus
    from app.domain.users import ObservedState, UserStatus
    from app.models.invitation import InvitationModel
    from app.models.user import UserModel, UserRuntimeBindingModel

    total_users = db.query(UserModel).count()
    active_users = db.query(UserModel).filter(UserModel.status == UserStatus.ACTIVE).count()
    disabled_users = db.query(UserModel).filter(UserModel.status == UserStatus.DISABLED).count()

    pending_invs = (
        db.query(InvitationModel)
        .filter(InvitationModel.status == InvitationStatus.PENDING)
        .count()
    )

    now = datetime.now(timezone.utc)
    in_24h = (now + timedelta(hours=24)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    expiring_24h = (
        db.query(InvitationModel)
        .filter(InvitationModel.status == InvitationStatus.PENDING)
        .filter(InvitationModel.expires_at <= in_24h)
        .count()
    )

    running_runtimes = (
        db.query(UserRuntimeBindingModel)
        .filter(UserRuntimeBindingModel.observed_state == ObservedState.RUNNING)
        .count()
    )
    runtime_errors = (
        db.query(UserRuntimeBindingModel)
        .filter(UserRuntimeBindingModel.observed_state == ObservedState.ERROR)
        .count()
    )

    pending_inv_rows = (
        db.query(InvitationModel)
        .filter(InvitationModel.status == InvitationStatus.PENDING)
        .order_by(InvitationModel.id.desc())
        .limit(10)
        .all()
    )
    pending_inv_items = [
        AdminInvitationItem(
            invitationId=r.invitation_id,
            targetEmail=r.target_email,
            loginUsername=r.login_username,
            workspaceId=r.workspace_id,
            role=r.role,
            status=r.status.value,
            expiresAt=r.expires_at,
            consumedAt=r.consumed_at,
            consumedByUserId=r.consumed_by_user_id,
            lastError=r.last_error,
            createdAt=r.created_at,
        )
        for r in pending_inv_rows
    ]

    runtime_alert_rows = (
        db.query(UserRuntimeBindingModel)
        .filter(UserRuntimeBindingModel.observed_state == ObservedState.ERROR)
        .order_by(UserRuntimeBindingModel.id.desc())
        .limit(10)
        .all()
    )
    runtime_alerts = [
        AdminHomeRuntimeAlert(
            userId=r.user_id,
            runtimeId=r.runtime_id,
            observedState=r.observed_state.value,
            lastError=r.last_error,
            updatedAt=_iso_now(),
        )
        for r in runtime_alert_rows
    ]

    return AdminHomeResponse(
        summary=AdminHomeSummary(
            totalUsers=total_users,
            activeUsers=active_users,
            disabledUsers=disabled_users,
            pendingInvitations=pending_invs,
            expiringInvitations24h=expiring_24h,
            runningRuntimes=running_runtimes,
            runtimeErrors=runtime_errors,
        ),
        attention=AdminHomeAttention(
            pendingInvitations=pending_inv_items,
            runtimeAlerts=runtime_alerts,
        ),
    )


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


