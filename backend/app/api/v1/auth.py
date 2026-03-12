from fastapi import APIRouter

from app.schemas.auth import AuthMeResponse, AccessCheckResponse


router = APIRouter(tags=["auth"])


@router.get("/auth/me", response_model=AuthMeResponse)
async def get_current_user() -> AuthMeResponse:
    """
    获取当前登录用户。

    TODO:
    - 从实际鉴权上下文中获取用户信息（对接 Authentik）。
    """
    # 占位返回示例用户，便于前后端联调。
    return AuthMeResponse(
        authenticated=True,
        user_id="u_001",
        subject_id="authentik:12345",
        tenant_id="t_default",
        role="user",
        is_admin=False,
        is_disabled=False,
    )


@router.get("/auth/access", response_model=AccessCheckResponse)
async def check_access() -> AccessCheckResponse:
    """
    检查当前用户是否可访问业务。

    TODO:
    - 根据用户状态（active/disabled）与角色判断访问权限。
    """
    return AccessCheckResponse(allowed=True, reason=None)

