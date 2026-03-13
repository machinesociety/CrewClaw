from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_user_service
from app.domain.users import DesiredState, ObservedState, RetentionPolicy
from app.schemas.internal import (
    SyncUserRequest,
    RuntimeBindingUpsertRequest,
    RuntimeBindingStateUpdateRequest,
    ModelConfigResponse,
    UsageRecordItem,
    EnsureContainerRequest,
    ContainerStateResponse,
)
from app.schemas.runtime import (
    DesiredState as SchemaDesiredState,
    ObservedState as SchemaObservedState,
    RetentionPolicy as SchemaRetentionPolicy,
    UserRuntimeBinding,
)
from app.services.user_service import UserService


router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/sync")
async def sync_user(
    body: SyncUserRequest,
    user_service: UserService = Depends(get_user_service),
) -> dict:
    """
    首次登录同步 / 创建用户。

    """
    user = user_service.get_or_create_user(body.subject_id)
    return {"userId": user.user_id, "subjectId": user.subject_id, "tenantId": user.tenant_id}


@router.post("/users/{user_id}/runtime-binding/ensure", response_model=UserRuntimeBinding)
async def ensure_runtime_binding(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
) -> UserRuntimeBinding:
    """
    确保 runtime binding 存在；首次创建时由模块 2 分配 runtimeId / volumeId / 默认 imageRef / 默认 retentionPolicy。
    """

    binding = user_service.ensure_runtime_binding(user_id)
    return UserRuntimeBinding(
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


@router.put("/users/{user_id}/runtime-binding")
async def upsert_runtime_binding(
    user_id: str,
    body: RuntimeBindingUpsertRequest,
    user_service: UserService = Depends(get_user_service),
) -> dict:
    """
    创建或更新 runtime binding。
    """
    desired = DesiredState(body.desired_state)
    observed = ObservedState(body.observed_state)
    retention = RetentionPolicy(body.retention_policy)
    user_service.upsert_runtime_binding(
        user_id=user_id,
        runtime_id=body.runtime_id,
        volume_id=body.volume_id,
        image_ref=body.image_ref,
        desired_state=desired,
        observed_state=observed,
        retention_policy=retention,
        browser_url=body.browser_url,
        internal_endpoint=body.internal_endpoint,
        last_error=body.last_error,
    )
    return {"status": "ok"}


@router.patch("/users/{user_id}/runtime-binding/state")
async def update_runtime_binding_state(
    user_id: str,
    body: RuntimeBindingStateUpdateRequest,
    user_service: UserService = Depends(get_user_service),
) -> dict:
    """
    更新 runtime binding 状态。
    """
    binding = user_service.update_runtime_binding_state(
        user_id=user_id,
        desired_state=DesiredState(body.desired_state),
        observed_state=ObservedState(body.observed_state),
        browser_url=body.browser_url,
        internal_endpoint=body.internal_endpoint,
        last_error=body.last_error,
    )
    if binding is None:
        raise HTTPException(status_code=404, detail="RUNTIME_NOT_FOUND")
    return {"status": "ok"}


@router.get("/model-config/users/{user_id}", response_model=ModelConfigResponse)
async def get_user_model_config(user_id: str) -> ModelConfigResponse:
    """
    获取运行时模型配置。
    """
    _ = user_id
    return ModelConfigResponse(
        base_url="http://litellm:4000",
        models=["gpt-4-mini"],
        gateway_access_token_ref="token_ref_001",
        config_render_version="v1",
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
        runtime_id="rt_001",
        observed_state="creating",
        internal_endpoint="http://crewclaw-u001:3000",
        message="creating",
    )


@router.post("/runtime-manager/containers/stop")
async def stop_container() -> dict:
    """
    停止容器占位。
    """
    return {"status": "accepted"}


@router.post("/runtime-manager/containers/delete")
async def delete_container() -> dict:
    """
    删除容器占位。
    """
    return {"status": "accepted"}


@router.get("/runtime-manager/containers/{runtime_id}", response_model=ContainerStateResponse)
async def get_container_state(runtime_id: str) -> ContainerStateResponse:
    """
    查询容器状态。
    """
    _ = runtime_id
    return ContainerStateResponse(
        runtime_id=runtime_id,
        observed_state="running",
        internal_endpoint="http://crewclaw-u001:3000",
        message="running",
    )

