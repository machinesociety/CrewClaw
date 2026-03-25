from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.core.dependencies import get_invitation_service, get_user_service
from app.core.errors import (
    InvitationEmailMismatchError,
    InvitationNotFoundError,
)
from app.domain.invitations import Invitation, InvitationStatus
from app.domain.users import DesiredState, ObservedState, RetentionPolicy
from app.schemas.internal import (
    ContainerStateResponse,
    DeleteContainerRequest,
    EnsureContainerRequest,
    ModelConfigResponse,
    RuntimeBindingStateUpdateRequest,
    RuntimeBindingUpsertRequest,
    StopContainerRequest,
    SyncUserRequest,
    UsageRecordItem,
)
from app.schemas.runtime import (
    DesiredState as SchemaDesiredState,
    ObservedState as SchemaObservedState,
    RetentionPolicy as SchemaRetentionPolicy,
    RuntimeBindingSnapshot,
)
from app.services.user_service import UserService
from app.services.invitation_service import InvitationService


router = APIRouter(prefix="/internal", tags=["internal"])


def _to_binding_snapshot(binding) -> RuntimeBindingSnapshot:
    return RuntimeBindingSnapshot(
        runtimeId=binding.runtime_id,
        volumeId=binding.volume_id,
        imageRef=binding.image_ref,
        desiredState=SchemaDesiredState(binding.desired_state.value),
        observedState=SchemaObservedState(binding.observed_state.value),
        browserUrl=binding.browser_url,
        internalEndpoint=binding.internal_endpoint,
        retentionPolicy=SchemaRetentionPolicy(binding.retention_policy.value),
        lastError=binding.last_error,
    )


@router.post("/users/sync")
async def sync_user(
    body: SyncUserRequest,
    user_service: UserService = Depends(get_user_service),
) -> dict:
    """
    首次登录同步 / 创建用户。

    """
    user = user_service.get_or_create_user(body.subjectId)
    return {"userId": user.user_id, "subjectId": user.subject_id, "tenantId": user.tenant_id}


@router.post("/invitations")
async def internal_create_invitation() -> dict:
    """
    internal 创建 invitation 真相对象（占位）。

    v0.11：管理员侧创建走 /api/v1/admin/invitations；这里保留 internal 落点以便后续模块拆分。
    """
    return {"status": "not_implemented"}


@router.post("/invitations/{invitation_id}/consume")
async def internal_consume_invitation(
    invitation_id: str,
    userId: str,
    email: str,
    svc: InvitationService = Depends(get_invitation_service),
) -> dict:
    """
    消费 invitation 并完成业务绑定（幂等骨架）。

    当前实现仅做：
    - invitation 存在性校验
    - 邮箱槽位校验（强校验）
    - 标记 consumed
    """
    inv = svc.consume(invitation_id=invitation_id, user_id=userId, email=email)
    return {"status": "ok", "invitationId": inv.invitation_id, "consumedByUserId": inv.consumed_by_user_id}


@router.post("/invitations/{invitation_id}/revoke")
async def internal_revoke_invitation(
    invitation_id: str,
    svc: InvitationService = Depends(get_invitation_service),
) -> dict:
    svc.revoke(invitation_id)
    return {"status": "ok"}

@router.post("/users/{user_id}/runtime-binding/ensure", response_model=RuntimeBindingSnapshot)
async def ensure_runtime_binding(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
) -> RuntimeBindingSnapshot:
    """
    确保 runtime binding 存在；首次创建时由模块 2 分配 runtimeId / volumeId / 默认 imageRef / 默认 retentionPolicy。
    """

    return _to_binding_snapshot(user_service.ensure_runtime_binding(user_id))


@router.put("/users/{user_id}/runtime-binding", response_model=RuntimeBindingSnapshot)
async def upsert_runtime_binding(
    user_id: str,
    body: RuntimeBindingUpsertRequest,
    user_service: UserService = Depends(get_user_service),
) -> RuntimeBindingSnapshot:
    """
    创建或更新 runtime binding。
    """
    desired = DesiredState(body.desiredState)
    observed = ObservedState(body.observedState)
    retention = RetentionPolicy(body.retentionPolicy)
    binding = user_service.upsert_runtime_binding(
        user_id=user_id,
        runtime_id=body.runtimeId,
        volume_id=body.volumeId,
        image_ref=body.imageRef,
        desired_state=desired,
        observed_state=observed,
        retention_policy=retention,
        browser_url=body.browserUrl,
        internal_endpoint=body.internalEndpoint,
        last_error=body.lastError,
    )
    return _to_binding_snapshot(binding)


@router.patch("/users/{user_id}/runtime-binding/state", response_model=RuntimeBindingSnapshot)
async def update_runtime_binding_state(
    user_id: str,
    body: RuntimeBindingStateUpdateRequest,
    user_service: UserService = Depends(get_user_service),
) -> RuntimeBindingSnapshot:
    """
    更新 runtime binding 状态。
    """
    binding = user_service.update_runtime_binding_state(
        user_id=user_id,
        desired_state=DesiredState(body.desiredState),
        observed_state=ObservedState(body.observedState),
        browser_url=body.browserUrl,
        internal_endpoint=body.internalEndpoint,
        last_error=body.lastError,
    )
    if binding is None:
        from app.core.errors import RuntimeNotFoundError

        raise RuntimeNotFoundError()
    return _to_binding_snapshot(binding)


@router.get("/model-config/users/{user_id}", response_model=ModelConfigResponse)
async def get_user_model_config(user_id: str) -> ModelConfigResponse:
    """
    获取运行时模型配置。
    """
    _ = user_id
    return ModelConfigResponse(
        baseUrl="http://litellm:4000",
        models=["gpt-4-mini"],
        gatewayAccessTokenRef="token_ref_001",
        configRenderVersion="v1",
    )


@router.post("/usage/records")
async def ingest_usage_records(records: list[UsageRecordItem]) -> dict:
    """
    接收 OpenClaw usage 上报。
    """
    _ = records
    return {"status": "accepted"}


@router.post("/runtime-manager/containers/ensure-running")
async def ensure_container_running(body: EnsureContainerRequest) -> ContainerStateResponse:
    """
    确保容器运行。

    TODO:
    - 调用 runtime-manager 客户端执行真实操作。
    """
    _ = body
    return ContainerStateResponse(
        runtimeId=body.runtimeId,
        observedState="creating",
        internalEndpoint=f"http://rt-{body.runtimeId}:18789",
        message="creating",
    )


@router.post("/runtime-manager/containers/stop")
async def stop_container(body: StopContainerRequest) -> dict:
    """
    停止容器占位。
    """
    # v0.11：stop(nonexistent)=stopped
    return {"runtimeId": body.runtimeId, "observedState": "stopped", "message": "stopped"}


@router.post("/runtime-manager/containers/delete")
async def delete_container(body: DeleteContainerRequest) -> dict:
    """
    删除容器占位。
    """
    _ = body.retentionPolicy
    # v0.11：delete(nonexistent)=deleted
    return {"runtimeId": body.runtimeId, "observedState": "deleted", "message": "deleted"}


@router.get("/runtime-manager/containers/{runtime_id}", response_model=ContainerStateResponse)
async def get_container_state(runtime_id: str) -> ContainerStateResponse:
    """
    查询容器状态。
    """
    _ = runtime_id
    # v0.11：GET 找不到容器事实时也返回 200 + observedState=deleted（此处用占位实现）。
    return ContainerStateResponse(
        runtimeId=runtime_id,
        observedState="deleted",
        internalEndpoint=None,
        message="deleted",
    )

