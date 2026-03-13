from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import AuthContext, build_auth_context_from_request
from app.core.database import get_db_session, init_db
from app.core.errors import UserDisabledError
from app.core.settings import AppSettings, get_settings
from app.repositories.user_repository import (
    InMemoryUserRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyUserRuntimeBindingRepository,
    UserRepository,
    UserRuntimeBindingRepository,
)
from app.services.user_service import UserService


_user_repo_singleton: UserRepository | None = None


def get_app_settings() -> AppSettings:
    return get_settings()


def get_user_repository() -> UserRepository:
    """
    默认返回基于 SQLAlchemy 的 UserRepository。

    测试中可以通过覆盖依赖或直接修改 _user_repo_singleton 来替换实现。
    """

    global _user_repo_singleton
    if _user_repo_singleton is not None:
        return _user_repo_singleton

    # 默认使用内存实现（主要用于早期阶段和某些测试场景）。
    return InMemoryUserRepository()


def get_db_session_dep() -> Session:
    """
    提供给 FastAPI 的 DB Session 依赖封装，便于在测试中覆盖。
    """

    # 确保表已创建。
    init_db()
    yield from get_db_session()


def get_runtime_binding_repository(
    db: Session = Depends(get_db_session_dep),
) -> UserRuntimeBindingRepository:
    return SqlAlchemyUserRuntimeBindingRepository(db)


def get_sqlalchemy_user_repository(
    db: Session = Depends(get_db_session_dep),
) -> UserRepository:
    return SqlAlchemyUserRepository(db)


def get_auth_context(
    request: Request,
    settings: AppSettings = Depends(get_app_settings),
    user_repo: UserRepository = Depends(get_sqlalchemy_user_repository),
) -> AuthContext:
    return build_auth_context_from_request(request, settings, user_repo)


def require_active_user(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if ctx.isDisabled:
        raise UserDisabledError()
    return ctx


def get_user_service(
    user_repo: UserRepository = Depends(get_sqlalchemy_user_repository),
    binding_repo: UserRuntimeBindingRepository = Depends(get_runtime_binding_repository),
    settings: AppSettings = Depends(get_app_settings),
) -> UserService:
    return UserService(
        user_repo=user_repo,
        binding_repo=binding_repo,
        default_image_ref="crewclaw-runtime-wrapper:openclaw-1.0.0",
        default_retention_policy="preserve_workspace",
    )


