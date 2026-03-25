from __future__ import annotations

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.invitations import InvitationStatus


class InvitationModel(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    invitation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    invite_token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    target_email: Mapped[str] = mapped_column(String(255), index=True)
    login_username: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    workspace_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(64))

    status: Mapped[InvitationStatus] = mapped_column(Enum(InvitationStatus), default=InvitationStatus.PENDING)
    expires_at: Mapped[str] = mapped_column(String(64))

    consumed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consumed_by_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    authentik_invitation_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

