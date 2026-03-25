from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import RedirectResponse

from app.core.auth import AuthContext
from app.core.dependencies import get_app_settings, get_auth_context, get_invitation_service, get_user_service
from app.core.settings import AppSettings
from app.core.errors import InvitationEmailMismatchError
from app.api.v1.invitations_public import PENDING_INV_COOKIE
from app.schemas.auth import AccessCheckResponse, AuthMeResponse, AuthOptionsResponse, AuthOption, SessionUser
from app.services.invitation_service import InvitationService
from app.services.user_service import UserService


router = APIRouter(tags=["auth"])


@router.get("/auth/me", response_model=AuthMeResponse)
async def get_current_user(ctx: AuthContext = Depends(get_auth_context)) -> AuthMeResponse:
    """获取当前登录用户，即使 disabled 也可访问。"""

    return AuthMeResponse(
        authenticated=True,
        user=SessionUser(
            userId=ctx.userId,
            subjectId=ctx.subjectId,
            tenantId=ctx.tenantId,
            role=ctx.role,
            status="disabled" if ctx.isDisabled else "active",
            auth={"provider": "authentik", "method": "local_password"},
            isAdmin=ctx.isAdmin,
            isDisabled=ctx.isDisabled,
        ),
    )


@router.get("/auth/access", response_model=AccessCheckResponse)
async def check_access(ctx: AuthContext = Depends(get_auth_context)) -> AccessCheckResponse:
    """检查当前用户是否可访问业务（永远返回 200）。"""

    if ctx.isDisabled:
        return AccessCheckResponse(allowed=False, reason="USER_DISABLED")
    return AccessCheckResponse(allowed=True, reason=None)


@router.get("/auth/options", response_model=AuthOptionsResponse)
async def get_auth_options() -> AuthOptionsResponse:
    """返回登录页可用认证方式。"""

    return AuthOptionsResponse(
        provider="authentik",
        methods=[AuthOption(type="local_password", enabled=True, label="用户名优先登录")],
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
    ctx: AuthContext = Depends(get_auth_context),
    user_service: UserService = Depends(get_user_service),
    invitation_service: InvitationService = Depends(get_invitation_service),
    pending_invitation_id: str | None = Cookie(default=None, alias=PENDING_INV_COOKIE),
) -> dict:
    """
    登录收口（幂等）：确保用户存在并返回前端跳转决策。
    """
    if ctx.isDisabled:
        from app.core.errors import UserDisabledError

        raise UserDisabledError()

    user_service.get_or_create_user(ctx.subjectId)

    # v0.11：admin 默认进入 /admin；普通用户默认进入 /app
    if ctx.isAdmin:
        return {"entryType": "admin_console", "redirectTo": "/admin", "hasWorkspace": False, "workspaceId": None}

    # v0.11：若存在 pending invitation，上游已登录后在此做邮箱槽位强校验并消费（当前仅做最小校验骨架）
    if pending_invitation_id:
        if not ctx.email:
            raise InvitationEmailMismatchError("Missing authenticated email slot.")
        invitation_service.consume(invitation_id=pending_invitation_id, user_id=ctx.userId, email=ctx.email)

    # MVP 阶段：尚未引入真实 workspace membership 时，先用 runtime binding 作为 hasWorkspace 的最小替代信号。
    # 后续在 invitation/membership 实现后，此处会以 membership 为真相。
    has_workspace = user_service.get_runtime_binding(ctx.userId) is not None
    return {"entryType": "workspace", "redirectTo": "/app", "hasWorkspace": has_workspace, "workspaceId": None}

