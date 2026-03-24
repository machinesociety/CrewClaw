from __future__ import annotations

from sqlalchemy import Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.users import DesiredState, ObservedState, RetentionPolicy, UserRole, UserStatus


class UserModel(Base):
    """
    用户表 ORM 模型，对应领域层 User。
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="t_default", index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)


class UserRuntimeBindingModel(Base):
    """
    UserRuntimeBinding 真相层 ORM 模型。

    每个 user 至多一条记录，通过 user_id 唯一约束保证。
    """

    __tablename__ = "user_runtime_bindings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_binding_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    runtime_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    volume_id: Mapped[str] = mapped_column(String(128))
    image_ref: Mapped[str] = mapped_column(String(255))

    desired_state: Mapped[DesiredState] = mapped_column(Enum(DesiredState))
    observed_state: Mapped[ObservedState] = mapped_column(Enum(ObservedState))

    browser_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    internal_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)

    retention_policy: Mapped[RetentionPolicy] = mapped_column(Enum(RetentionPolicy))
    last_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

