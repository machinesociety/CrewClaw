from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.domain.invitations import Invitation, InvitationStatus
from app.models.invitation import InvitationModel


class InvitationRepository(ABC):
    @abstractmethod
    def get_by_id(self, invitation_id: str) -> Invitation | None: ...

    @abstractmethod
    def get_by_token_hash(self, invite_token_hash: str) -> Invitation | None: ...

    @abstractmethod
    def list_all(self) -> list[Invitation]: ...

    @abstractmethod
    def save(self, inv: Invitation) -> None: ...


class SqlAlchemyInvitationRepository(InvitationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, invitation_id: str) -> Invitation | None:
        row = (
            self._session.query(InvitationModel)
            .filter(InvitationModel.invitation_id == invitation_id)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_token_hash(self, invite_token_hash: str) -> Invitation | None:
        row = (
            self._session.query(InvitationModel)
            .filter(InvitationModel.invite_token_hash == invite_token_hash)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def list_all(self) -> list[Invitation]:
        rows = self._session.query(InvitationModel).order_by(InvitationModel.id.desc()).all()
        return [self._to_domain(r) for r in rows]

    def save(self, inv: Invitation) -> None:
        row = (
            self._session.query(InvitationModel)
            .filter(InvitationModel.invitation_id == inv.invitation_id)
            .one_or_none()
        )
        if row is None:
            row = InvitationModel(
                invitation_id=inv.invitation_id,
                invite_token_hash=inv.invite_token_hash,
                target_email=inv.target_email,
                login_username=inv.login_username,
                workspace_id=inv.workspace_id,
                role=inv.role,
                status=InvitationStatus(inv.status.value),
                expires_at=inv.expires_at,
                consumed_at=inv.consumed_at,
                consumed_by_user_id=inv.consumed_by_user_id,
                authentik_invitation_ref=inv.authentik_invitation_ref,
                last_error=inv.last_error,
                created_at=inv.created_at,
                created_by_user_id=inv.created_by_user_id,
            )
            self._session.add(row)
        else:
            row.invite_token_hash = inv.invite_token_hash
            row.target_email = inv.target_email
            row.login_username = inv.login_username
            row.workspace_id = inv.workspace_id
            row.role = inv.role
            row.status = InvitationStatus(inv.status.value)
            row.expires_at = inv.expires_at
            row.consumed_at = inv.consumed_at
            row.consumed_by_user_id = inv.consumed_by_user_id
            row.authentik_invitation_ref = inv.authentik_invitation_ref
            row.last_error = inv.last_error
            row.created_at = inv.created_at
            row.created_by_user_id = inv.created_by_user_id

        self._session.commit()

    @staticmethod
    def _to_domain(row: InvitationModel) -> Invitation:
        return Invitation(
            invitation_id=row.invitation_id,
            invite_token_hash=row.invite_token_hash,
            target_email=row.target_email,
            login_username=row.login_username,
            workspace_id=row.workspace_id,
            role=row.role,
            status=row.status,
            expires_at=row.expires_at,
            consumed_at=row.consumed_at,
            consumed_by_user_id=row.consumed_by_user_id,
            authentik_invitation_ref=row.authentik_invitation_ref,
            last_error=row.last_error,
            created_at=row.created_at,
            created_by_user_id=row.created_by_user_id,
        )

