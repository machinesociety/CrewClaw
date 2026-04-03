from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InvitationModel(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invitation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    invite_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    target_email: Mapped[str] = mapped_column(String(255))
    login_username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    workspace_id: Mapped[str] = mapped_column(String(64))
    workspace_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))

    status: Mapped[str] = mapped_column(String(32))  # pending | consumed | revoked
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    consumed_by_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

