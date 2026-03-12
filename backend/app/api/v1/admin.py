from fastapi import APIRouter

from app.schemas.admin import (
    UpdateUserStatusRequest,
    AdminUserRuntimeResponse,
    AdminUserCredentialsResponse,
    AdminUsageSummaryResponse,
)


router = APIRouter(tags=["admin"])


@router.patch("/admin/users/{user_id}/status")
async def update_user_status(user_id: str, body: UpdateUserStatusRequest) -> dict:
    """
    启用 / 禁用用户。

    TODO:
    - 调用 UserService 更新用户状态并触发 runtime 收敛。
    """
    _ = (user_id, body)
    return {"userId": user_id, "status": body.status}


@router.get("/admin/users/{user_id}/runtime", response_model=AdminUserRuntimeResponse)
async def get_admin_user_runtime(user_id: str) -> AdminUserRuntimeResponse:
    """
    管理员查看指定用户的 runtime。
    """
    _ = user_id
    return AdminUserRuntimeResponse(
        runtime_id="rt_001",
        desired_state="running",
        observed_state="running",
        browser_url="https://u-001.crewclaw.example.com",
        internal_endpoint="http://crewclaw-u001:3000",
        last_error=None,
    )


@router.get("/admin/users/{user_id}/credentials", response_model=AdminUserCredentialsResponse)
async def get_admin_user_credentials(user_id: str) -> AdminUserCredentialsResponse:
    """
    管理员查看指定用户的凭据元数据。
    """
    _ = user_id
    return AdminUserCredentialsResponse(credentials=[])


@router.get("/admin/usage/summary", response_model=AdminUsageSummaryResponse)
async def get_admin_usage_summary() -> AdminUsageSummaryResponse:
    """
    管理员查看平台 usage 汇总。
    """
    return AdminUsageSummaryResponse(total_tokens=10_000_000, used_tokens=123_456)

