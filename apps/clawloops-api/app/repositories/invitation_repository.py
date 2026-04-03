from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.invitation import InvitationModel


class InvitationRecord:
    def __init__(
        self,
        *,
        invitation_id: str,
        invite_token_hash: str,
        target_email: str,
        login_username: str | None,
        workspace_id: str,
        workspace_name: str,
        role: str,
        status: str,
        expires_at: datetime,
        consumed_by_user_id: str | None,
        consumed_at: datetime | None,
    ) -> None:
        self.invitation_id = invitation_id
        self.invite_token_hash = invite_token_hash
        self.target_email = target_email
        self.login_username = login_username
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name
        self.role = role
        self.status = status
        self.expires_at = expires_at
        self.consumed_by_user_id = consumed_by_user_id
        self.consumed_at = consumed_at


class InvitationRepository(ABC):
    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> InvitationRecord | None: ...

    @abstractmethod
    def get_by_invitation_id(self, invitation_id: str) -> InvitationRecord | None: ...

    @abstractmethod
    def consume_idempotent(
        self,
        *,
        invitation_id: str,
        consumed_by_user_id: str,
        now: datetime,
    ) -> tuple[InvitationRecord, bool]:
        """
        返回 (record, replayed)。
        """


class SqlAlchemyInvitationRepository(InvitationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_token_hash(self, token_hash: str) -> InvitationRecord | None:
        row = (
            self._session.query(InvitationModel)
            .filter(InvitationModel.invite_token_hash == token_hash)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_record(row)

    def get_by_invitation_id(self, invitation_id: str) -> InvitationRecord | None:
        row = (
            self._session.query(InvitationModel)
            .filter(InvitationModel.invitation_id == invitation_id)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_record(row)

    def consume_idempotent(
        self,
        *,
        invitation_id: str,
        consumed_by_user_id: str,
        now: datetime,
    ) -> tuple[InvitationRecord, bool]:
        row = (
            self._session.query(InvitationModel)
            .filter(InvitationModel.invitation_id == invitation_id)
            .one_or_none()
        )
        if row is None:
            raise ValueError("invitation not found")

        # Already consumed
        if row.status == "consumed":
            replayed = row.consumed_by_user_id == consumed_by_user_id
            return self._to_record(row), replayed

        # Revoked invitations should not be consumed
        if row.status == "revoked":
            return self._to_record(row), False

        row.status = "consumed"
        row.consumed_by_user_id = consumed_by_user_id
        row.consumed_at = now
        self._session.commit()
        return self._to_record(row), False

    @staticmethod
    def _to_record(row: InvitationModel) -> InvitationRecord:
        return InvitationRecord(
            invitation_id=row.invitation_id,
            invite_token_hash=row.invite_token_hash,
            target_email=row.target_email,
            login_username=row.login_username,
            workspace_id=row.workspace_id,
            workspace_name=row.workspace_name,
            role=row.role,
            status=row.status,
            expires_at=row.expires_at,
            consumed_by_user_id=row.consumed_by_user_id,
            consumed_at=row.consumed_at,
        )

