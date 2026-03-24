from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import get_auth_context, require_active_user
from app.schemas.auth import AccessCheckResponse, AuthMeResponse, AuthOptionsResponse, AuthOption


router = APIRouter(tags=["auth"])


@router.get("/auth/me", response_model=AuthMeResponse)
async def get_current_user(ctx: AuthContext = Depends(get_auth_context)) -> AuthMeResponse:
    """获取当前登录用户，即使 disabled 也可访问。"""

    return AuthMeResponse(
        authenticated=True,
        userId=ctx.userId,
        subjectId=ctx.subjectId,
        tenantId=ctx.tenantId,
        role=ctx.role,
        isAdmin=ctx.isAdmin,
        isDisabled=ctx.isDisabled,
    )


@router.get("/auth/access", response_model=AccessCheckResponse)
async def check_access(ctx: AuthContext = Depends(require_active_user)) -> AccessCheckResponse:
    """检查当前用户是否可访问业务。"""

    return AccessCheckResponse(allowed=True, reason=None)


@router.get("/auth/options", response_model=AuthOptionsResponse)
async def get_auth_options() -> AuthOptionsResponse:
    """返回登录页可用认证方式。"""

    return AuthOptionsResponse(
        provider="authentik",
        methods=[AuthOption(type="local_password", enabled=True, label="账号密码登录")],
    )

