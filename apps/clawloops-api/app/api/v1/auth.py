from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.core.auth import AuthContext
from app.core.dependencies import get_app_settings, get_auth_context, get_user_service, require_active_user
from app.core.settings import AppSettings
from app.schemas.auth import AccessCheckResponse, AuthMeResponse, AuthOptionsResponse, AuthOption
from app.services.user_service import UserService


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


@router.get("/auth/login")
async def auth_login(
    settings: AppSettings = Depends(get_app_settings),
) -> RedirectResponse:
    """
    通过 Authentik outpost 发起登录，登录完成后回到前端 /post-login 页面。
    """
    rd = quote(settings.auth_post_login_redirect_url, safe="")
    login_url = f"/outpost.goauthentik.io/start?rd={rd}"
    return RedirectResponse(url=login_url, status_code=302)


@router.post("/auth/post-login")
async def auth_post_login(
    ctx: AuthContext = Depends(require_active_user),
    user_service: UserService = Depends(get_user_service),
) -> dict:
    """
    登录收口（幂等）：确保用户存在并返回前端跳转决策。
    """
    user_service.get_or_create_user(ctx.subjectId)
    binding = user_service.get_runtime_binding(ctx.userId)
    has_workspace = binding is not None
    return {
        "status": "ok",
        "result": "ok",
        "userId": ctx.userId,
        "hasWorkspace": has_workspace,
        "needsWorkspaceSelection": False,
        "redirectTo": "/workspace-entry" if has_workspace else None,
    }

