from fastapi import APIRouter

from app.schemas.runtime import (
    UserQuotaResponse,
    UserRuntimeBindingResponse,
    RuntimeStatusResponse,
)


router = APIRouter(tags=["users"])


@router.get("/users/me/quota", response_model=UserQuotaResponse)
async def get_my_quota() -> UserQuotaResponse:
    """
    获取当前用户 quota。

    TODO:
    - 从实际配额服务或配置中读取。
    """
    return UserQuotaResponse(
        user_id="u_001",
        total_tokens=1_000_000,
        used_tokens=12_345,
    )


@router.get("/users/me/runtime", response_model=UserRuntimeBindingResponse | None)
async def get_my_runtime_binding() -> UserRuntimeBindingResponse | None:
    """
    获取当前用户 runtime binding。

    TODO:
    - 从 UserRuntimeBinding 仓储中读取实际数据。
    """
    return UserRuntimeBindingResponse(
        user_id="u_001",
        runtime_id="rt_001",
        volume_id="vol_001",
        image_ref="crewclaw-runtime-wrapper:openclaw-1.0.0",
        desired_state="running",
        observed_state="running",
        browser_url="https://u-001.crewclaw.example.com",
        internal_endpoint="http://crewclaw-u001:3000",
        retention_policy="preserve_workspace",
        last_error=None,
    )


@router.get("/users/me/runtime/status", response_model=RuntimeStatusResponse)
async def get_my_runtime_status() -> RuntimeStatusResponse:
    """
    查询当前用户 runtime 状态。

    TODO:
    - 从 RuntimeTask 和 UserRuntimeBinding 综合得出状态。
    """
    return RuntimeStatusResponse(
        runtime_id="rt_001",
        desired_state="running",
        observed_state="running",
        browser_url="https://u-001.crewclaw.example.com",
        last_error=None,
    )

