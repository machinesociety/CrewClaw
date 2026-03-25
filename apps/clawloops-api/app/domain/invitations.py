from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InvitationStatus(str, Enum):
    PENDING = "pending"
    CONSUMED = "consumed"
    REVOKED = "revoked"


@dataclass(slots=True)
class Invitation:
    invitation_id: str
    invite_token_hash: str
    target_email: str
    login_username: str | None
    workspace_id: str
    role: str
    status: InvitationStatus
    expires_at: str
    consumed_at: str | None = None
    consumed_by_user_id: str | None = None
    authentik_invitation_ref: str | None = None
    last_error: str | None = None
    created_at: str | None = None
    created_by_user_id: str | None = None

