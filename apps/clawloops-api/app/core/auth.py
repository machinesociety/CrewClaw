from fastapi import Request
from pydantic import BaseModel

from app.core.authentik_groups import (
    effective_role_from_groups,
    parse_admin_group_slugs,
    parse_authentik_groups,
    parse_group_names_from_authentik_jwt,
)
from app.core.errors import UnauthenticatedError
from app.core.settings import AppSettings
from app.domain.users import User, UserRole, UserStatus
from app.repositories.user_repository import UserRepository


class AuthContext(BaseModel):
    """当前请求的认证上下文，与基线契约字段对齐。"""

    userId: str
    subjectId: str
    tenantId: str
    role: str
    email: str | None = None
    username: str | None = None
    isAdmin: bool = False
    isDisabled: bool = False


def _read_first_header(request: Request, *names: str) -> str | None:
    for n in names:
        v = request.headers.get(n)
        if v:
            return v
    return None


def _read_groups_header(request: Request, settings: AppSettings) -> str | None:
    """返回组头原始字符串；未发送该头时为 None（与空字符串区分）。"""
    for name in (
        settings.auth_header_groups,
        "X-Authentik-Groups",
        "x-authentik-groups",
    ):
        if name in request.headers:
            return request.headers[name]
    return None


def _read_jwt_header(request: Request) -> str | None:
    """返回 X-authentik-jwt；未发送时为 None。"""
    for name in ("X-Authentik-Jwt", "x-authentik-jwt", "X-authentik-JWT"):
        if name in request.headers:
            return request.headers[name]
    return None


def build_auth_context_from_request(
    request: Request,
    settings: AppSettings,
    user_repo: UserRepository,
) -> AuthContext:
    """
    根据请求头与用户仓储构造 AuthContext。

    - 若缺少 subject 头部则视为未认证。
    - 若用户不存在，则以默认值创建（tenantId=t_default, role=user, status=active）。
    - 若请求携带 X-Authentik-Groups（含空值），则按组同步应用内 role。
    - 若未携带该头但携带 X-authentik-jwt，则从 JWT payload 的 claims.groups 解析组名并同步（Traefik/Outpost 可能只透传 JWT）。
    - 若两者均不能提供可解析的组信息，则不修改已有 role。
    """

    configured_subject_header = settings.auth_header_subject
    candidate_headers = [
        configured_subject_header,
        "X-authentik-uid",
        "X-Authentik-Uid",
        "X-Authentik-Subject",
    ]
    subject_id = None
    for header_name in candidate_headers:
        subject_id = request.headers.get(header_name)
        if subject_id:
            break
    if not subject_id:
        raise UnauthenticatedError()

    user = user_repo.get_by_subject_id(subject_id)
    if user is None:
        # 按 MVP 约定创建默认用户，后续可委托模块 2 的 /internal/users/sync。
        user = User(
            user_id=f"auto_{abs(hash(subject_id))}",
            subject_id=subject_id,
            tenant_id="t_default",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        user_repo.save(user)

    admin_slugs = parse_admin_group_slugs(settings.auth_admin_group_slugs)
    groups_header = _read_groups_header(request, settings)
    jwt_token = _read_jwt_header(request)
    group_names: list[str] | None = None

    if groups_header is not None:
        group_names = parse_authentik_groups(groups_header)
    elif jwt_token:
        parsed_jwt = parse_group_names_from_authentik_jwt(jwt_token)
        if parsed_jwt is not None:
            group_names = parsed_jwt

    if group_names is not None:
        desired = effective_role_from_groups(group_names, admin_slugs)
        if user.role != desired:
            user.role = desired
            user_repo.save(user)

    email = _read_first_header(
        request,
        settings.auth_header_email,
        "X-authentik-email",
        "X-Authentik-Email",
    )
    username = _read_first_header(
        request,
        "X-authentik-username",
        "X-Authentik-Username",
        "X-authentik-name",
        "X-Authentik-Name",
    )

    return AuthContext(
        userId=user.user_id,
        subjectId=user.subject_id,
        tenantId=user.tenant_id,
        role=user.role.value,
        email=email,
        username=username,
        isAdmin=user.role == UserRole.ADMIN,
        isDisabled=user.is_disabled(),
    )

