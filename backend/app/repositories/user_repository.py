from abc import ABC, abstractmethod
from typing import Protocol

from sqlalchemy.orm import Session

from app.domain.users import (
    DesiredState,
    ObservedState,
    RetentionPolicy,
    User,
    UserRuntimeBinding,
    UserRole,
    UserStatus,
)
from app.models.user import UserModel, UserRuntimeBindingModel


class UserRepository(ABC):
    """
    User 持久化仓储接口。

    TODO:
    - 提供数据库实现（如基于 SQLAlchemy）。
    """

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    def get_by_subject_id(self, subject_id: str) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> None: ...


class UserRuntimeBindingRepository(Protocol):
    """
    UserRuntimeBinding 持久化接口。

    TODO:
    - 定义与实现完整的 CRUD 操作。
    """

    def get_by_user_id(self, user_id: str) -> UserRuntimeBinding | None: ...

    def save(self, binding: UserRuntimeBinding) -> None: ...


class InMemoryUserRepository(UserRepository):
    """
    内存版用户仓储，便于开发与单元测试。
    """

    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def get_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_subject_id(self, subject_id: str) -> User | None:
        return next((u for u in self._users.values() if u.subject_id == subject_id), None)

    def save(self, user: User) -> None:
        self._users[user.user_id] = user


class SqlAlchemyUserRepository(UserRepository):
    """
    基于 SQLAlchemy 的 User 仓储实现。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: str) -> User | None:
        row = (
            self._session.query(UserModel)
            .filter(UserModel.user_id == user_id)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_subject_id(self, subject_id: str) -> User | None:
        row = (
            self._session.query(UserModel)
            .filter(UserModel.subject_id == subject_id)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def save(self, user: User) -> None:
        row = (
            self._session.query(UserModel)
            .filter(UserModel.user_id == user.user_id)
            .one_or_none()
        )
        if row is None:
            row = UserModel(
                user_id=user.user_id,
                subject_id=user.subject_id,
                tenant_id=user.tenant_id,
                role=user.role,
                status=user.status,
            )
            self._session.add(row)
        else:
            row.subject_id = user.subject_id
            row.tenant_id = user.tenant_id
            row.role = user.role
            row.status = user.status

        self._session.commit()

    @staticmethod
    def _to_domain(row: UserModel) -> User:
        return User(
            user_id=row.user_id,
            subject_id=row.subject_id,
            tenant_id=row.tenant_id,
            role=row.role,
            status=row.status,
        )


class SqlAlchemyUserRuntimeBindingRepository(UserRuntimeBindingRepository):
    """
    基于 SQLAlchemy 的 UserRuntimeBinding 仓储实现。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_user_id(self, user_id: str) -> UserRuntimeBinding | None:
        row = (
            self._session.query(UserRuntimeBindingModel)
            .filter(UserRuntimeBindingModel.user_id == user_id)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def save(self, binding: UserRuntimeBinding) -> None:
        row = (
            self._session.query(UserRuntimeBindingModel)
            .filter(UserRuntimeBindingModel.user_id == binding.user_id)
            .one_or_none()
        )
        if row is None:
            row = UserRuntimeBindingModel(
                user_id=binding.user_id,
                runtime_id=binding.runtime_id,
                volume_id=binding.volume_id,
                image_ref=binding.image_ref,
                desired_state=binding.desired_state,
                observed_state=binding.observed_state,
                browser_url=binding.browser_url,
                internal_endpoint=binding.internal_endpoint,
                retention_policy=binding.retention_policy,
                last_error=binding.last_error,
            )
            self._session.add(row)
        else:
            row.runtime_id = binding.runtime_id
            row.volume_id = binding.volume_id
            row.image_ref = binding.image_ref
            row.desired_state = binding.desired_state
            row.observed_state = binding.observed_state
            row.browser_url = binding.browser_url
            row.internal_endpoint = binding.internal_endpoint
            row.retention_policy = binding.retention_policy
            row.last_error = binding.last_error

        self._session.commit()

    @staticmethod
    def _to_domain(row: UserRuntimeBindingModel) -> UserRuntimeBinding:
        return UserRuntimeBinding(
            user_id=row.user_id,
            runtime_id=row.runtime_id,
            volume_id=row.volume_id,
            image_ref=row.image_ref,
            desired_state=row.desired_state,
            observed_state=row.observed_state,
            retention_policy=row.retention_policy,
            browser_url=row.browser_url,
            internal_endpoint=row.internal_endpoint,
            last_error=row.last_error,
        )


