from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response

from app.core.auth import AuthContext
from app.core.dependencies import (
    get_app_settings,
    get_auth_context,
    get_session_repository,
    get_sqlalchemy_user_repository,
    try_get_auth_context,
)
from app.core.errors import (
    CurrentPasswordIncorrectError,
    InvalidCredentialsError,
    PasswordChangeInvalidError,
    UserDisabledError,
)
from app.core.password_policy import validate_password_policy
from app.core.passwords import hash_password_pbkdf2_sha256, verify_password_pbkdf2_sha256
from app.core.sessions import create_session, hash_session_token
from app.core.settings import AppSettings
from app.domain.users import User, UserRole, UserStatus
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AccessCheckResponse,
    AuthFeatures,
    AuthMeResponse,
    AuthOptionsResponse,
    AuthOption,
    LoginRequest,
    LoginResult,
    LogoutResult,
    PasswordChangeRequest,
    PasswordChangeResult,
    PasswordPolicy,
    SessionAuthInfo,
    SessionUser,
)


router = APIRouter(tags=["auth"])


def _set_session_cookie(resp: Response, settings: AppSettings, token: str) -> None:
    resp.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )


def _clear_session_cookie(resp: Response, settings: AppSettings) -> None:
    resp.delete_cookie(
        key=settings.session_cookie_name,
        domain=settings.cookie_domain,
        path="/",
    )


def _to_session_user(ctx: AuthContext) -> SessionUser:
    return SessionUser(
        userId=ctx.userId,
        subjectId=ctx.subjectId,
        username=ctx.username,
        tenantId=ctx.tenantId,
        role=ctx.role,  # 'admin' | 'user'
        status=ctx.status,  # 'active' | 'disabled'
        auth=SessionAuthInfo(provider="clawloops", method="local_password"),
        isAdmin=ctx.isAdmin,
        isDisabled=ctx.isDisabled,
        mustChangePassword=ctx.mustChangePassword,
        passwordChangeReason=ctx.passwordChangeReason,
    )


def _ensure_seed_admin(user_repo: UserRepository) -> User:
    """
    首版：若数据库中不存在 seed admin，则按文档创建。
    - username=admin
    - 初始密码=admin
    - must_change_password=true
    """
    existing = user_repo.get_by_username("admin")
    if existing is not None:
        return existing

    now = datetime.now(timezone.utc)
    user = User(
        user_id="u_seed_admin",
        subject_id="clawloops:u_seed_admin",
        tenant_id="t_default",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        username="admin",
        password_hash=hash_password_pbkdf2_sha256("admin"),
        must_change_password=True,
        password_change_reason="SEED_ADMIN_FIRST_LOGIN",
        created_at=now,
        last_login_at=None,
    )
    user_repo.save(user)
    return user


@router.get("/auth/me", response_model=AuthMeResponse)
async def get_current_user(
    ctx: AuthContext | None = Depends(try_get_auth_context),
) -> AuthMeResponse:
    """
    获取当前登录用户（v0.12）。

    说明：前端启动阶段依赖它判断是否存在 session。若无 session，则返回 authenticated=false。
    """
    if ctx is None:
        return AuthMeResponse(authenticated=False, user=None)
    return AuthMeResponse(authenticated=True, user=_to_session_user(ctx))


@router.get("/auth/access", response_model=AccessCheckResponse)
async def check_access(
    ctx: AuthContext | None = Depends(try_get_auth_context),
) -> AccessCheckResponse:
    """检查当前用户是否可访问业务（永远 200）。"""
    if ctx is None:
        return AccessCheckResponse(allowed=False, reason=None)
    if ctx.isDisabled:
        return AccessCheckResponse(allowed=False, reason="USER_DISABLED")
    if ctx.mustChangePassword:
        return AccessCheckResponse(allowed=False, reason="PASSWORD_CHANGE_REQUIRED")
    return AccessCheckResponse(allowed=True, reason=None)


@router.get("/auth/options", response_model=AuthOptionsResponse)
async def get_auth_options() -> AuthOptionsResponse:
    """返回登录页可用认证方式。"""

    return AuthOptionsResponse(
        provider="clawloops",
        methods=[AuthOption(type="local_password", enabled=True, label="用户名优先登录")],
        passwordPolicy=PasswordPolicy(
            minLength=8,
            maxLength=64,
            requireLetter=True,
            requireNumber=True,
            disallowUsernameAsPassword=True,
            disallowDefaultAdminPassword=True,
        ),
        features=AuthFeatures(
            forcedPasswordChange=True,
            passwordRecovery=False,
            thirdPartyLogin=False,
        ),
    )


@router.post("/auth/login", response_model=LoginResult)
async def login(
    body: LoginRequest,
    response: Response,
    settings: AppSettings = Depends(get_app_settings),
    user_repo: UserRepository = Depends(get_sqlalchemy_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> LoginResult:
    """
    用户名密码登录（v0.12）。
    成功后写入 session cookie：clawloops_session。
    """
    if body.username == "admin":
        _ensure_seed_admin(user_repo)

    user = user_repo.get_by_username(body.username)
    if user is None:
        raise InvalidCredentialsError()
    if user.is_disabled():
        raise UserDisabledError()
    if not user.password_hash or not verify_password_pbkdf2_sha256(body.password, user.password_hash):
        raise InvalidCredentialsError()

    now = datetime.now(timezone.utc)
    user.last_login_at = now
    user_repo.save(user)

    new_sess = create_session(ttl_seconds=settings.session_ttl_seconds)
    session_repo.create(
        user_id=user.user_id,
        session_id_hash=new_sess.token_hash,
        issued_at=new_sess.issued_at,
        expires_at=new_sess.expires_at,
        created_by_ip=None,
        user_agent=None,
    )
    _set_session_cookie(response, settings, new_sess.token)

    ctx = AuthContext(
        userId=user.user_id,
        subjectId=user.subject_id,
        username=user.username,
        tenantId=user.tenant_id,
        role=user.role.value,
        status=user.status.value,
        auth={"provider": "clawloops", "method": "local_password"},
        isAdmin=user.role == UserRole.ADMIN,
        isDisabled=user.is_disabled(),
        mustChangePassword=user.must_change_password,
        passwordChangeReason=user.password_change_reason,
    )

    if ctx.mustChangePassword:
        return LoginResult(
            redirectTo="/force-password-change",
            mustChangePassword=True,
            user=_to_session_user(ctx),
        )
    if ctx.isAdmin:
        return LoginResult(redirectTo="/admin", mustChangePassword=False, user=_to_session_user(ctx))
    return LoginResult(redirectTo="/app", mustChangePassword=False, user=_to_session_user(ctx))


@router.post("/auth/logout", response_model=LogoutResult)
async def logout(
    request: Request,
    response: Response,
    settings: AppSettings = Depends(get_app_settings),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> LogoutResult:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        session_repo.revoke(hash_session_token(token), revoked_at=datetime.now(timezone.utc))
    _clear_session_cookie(response, settings)
    return LogoutResult(ok=True)


@router.post("/auth/password/change", response_model=PasswordChangeResult)
async def change_password(
    body: PasswordChangeRequest,
    request: Request,
    response: Response,
    settings: AppSettings = Depends(get_app_settings),
    ctx: AuthContext = Depends(get_auth_context),
    user_repo: UserRepository = Depends(get_sqlalchemy_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> PasswordChangeResult:
    user = user_repo.get_by_id(ctx.userId)
    if user is None or not user.password_hash:
        raise InvalidCredentialsError()
    if not verify_password_pbkdf2_sha256(body.currentPassword, user.password_hash):
        raise CurrentPasswordIncorrectError()
    if body.newPassword != body.newPasswordConfirm:
        raise PasswordChangeInvalidError("Password confirmation does not match.")
    if body.newPassword == body.currentPassword:
        raise PasswordChangeInvalidError("New password must be different from current password.")
    if not validate_password_policy(username=user.username or "", password=body.newPassword):
        raise PasswordChangeInvalidError()

    now = datetime.now(timezone.utc)
    user.password_hash = hash_password_pbkdf2_sha256(body.newPassword)
    user.must_change_password = False
    user.password_change_reason = None
    user.last_login_at = now
    user_repo.save(user)

    # 轮换 session：撤销旧 session + 创建新 session 并覆盖 cookie
    old_token = request.cookies.get(settings.session_cookie_name)
    if old_token:
        session_repo.revoke(hash_session_token(old_token), revoked_at=now)
    new_sess = create_session(ttl_seconds=settings.session_ttl_seconds)
    session_repo.create(
        user_id=user.user_id,
        session_id_hash=new_sess.token_hash,
        issued_at=new_sess.issued_at,
        expires_at=new_sess.expires_at,
        created_by_ip=None,
        user_agent=None,
    )
    _set_session_cookie(response, settings, new_sess.token)

    new_ctx = AuthContext(
        userId=user.user_id,
        subjectId=user.subject_id,
        username=user.username,
        tenantId=user.tenant_id,
        role=user.role.value,
        status=user.status.value,
        auth={"provider": "clawloops", "method": "local_password"},
        isAdmin=user.role == UserRole.ADMIN,
        isDisabled=user.is_disabled(),
        mustChangePassword=user.must_change_password,
        passwordChangeReason=user.password_change_reason,
    )
    redirect = "/admin" if new_ctx.isAdmin else "/app"
    return PasswordChangeResult(changed=True, redirectTo=redirect, user=_to_session_user(new_ctx))

