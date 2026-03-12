from abc import ABC, abstractmethod
from typing import Protocol

from app.domain.users import User, UserRuntimeBinding


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

