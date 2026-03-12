from fastapi import APIRouter

from app.schemas.internal import (
    SyncUserRequest,
    RuntimeBindingUpsertRequest,
    RuntimeBindingStateUpdateRequest,
    ModelConfigResponse,
    UsageRecordItem,
    EnsureContainerRequest,
    ContainerStateResponse,
)


router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/sync")
async def sync_user(body: SyncUserRequest) -> dict:
    """
    首次登录同步 / 创建用户。

    TODO:
    - 调用 UserService 以 subjectId 幂等创建用户。
    """
    _ = body
    return {"status": "ok"}


@router.put("/users/{user_id}/runtime-binding")
async def upsert_runtime_binding(user_id: str, body: RuntimeBindingUpsertRequest) -> dict:
    """
    创建或更新 runtime binding。
    """
    _ = (user_id, body)
    return {"status": "ok"}


@router.patch("/users/{user_id}/runtime-binding/state")
async def update_runtime_binding_state(user_id: str, body: RuntimeBindingStateUpdateRequest) -> dict:
    """
    更新 runtime binding 状态。
    """
    _ = (user_id, body)
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

