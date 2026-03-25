from __future__ import annotations

import hashlib
import secrets
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from app.core.errors import (
    InvitationAlreadyConsumedError,
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationRevokedError,
)
from app.core.settings import AppSettings
from app.domain.invitations import Invitation, InvitationStatus
from app.repositories.invitation_repository import InvitationRepository


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class InvitationService:
    def __init__(self, repo: InvitationRepository, settings: AppSettings) -> None:
        self._repo = repo
        self._settings = settings

    def create_admin_invitation(
        self,
        *,
        target_email: str,
        login_username: str | None,
        workspace_id: str,
        role: str,
        expires_in_hours: int,
        created_by_user_id: str | None,
    ) -> Invitation:
        # MVP：为避免在平台侧保存明文 token，同时便于管理员随时复制链接，
        # 先把 platform token 固定为 invitationId（通过状态机保证一次性消费）。
        invitation_id = f"inv_{secrets.token_hex(8)}"
        token_hash = sha256_hex(invitation_id)

        now = _now_utc()
        inv = Invitation(
            invitation_id=invitation_id,
            invite_token_hash=token_hash,
            target_email=target_email.strip().lower(),
            login_username=login_username.strip() if login_username and login_username.strip() else None,
            workspace_id=workspace_id.strip(),
            role=role.strip(),
            status=InvitationStatus.PENDING,
            expires_at=_iso(now + timedelta(hours=max(1, int(expires_in_hours)))),
            consumed_at=None,
            consumed_by_user_id=None,
            authentik_invitation_ref=None,
            last_error=None,
            created_at=_iso(now),
            created_by_user_id=created_by_user_id,
        )
        self._repo.save(inv)
        return inv

    def list_invitations(self) -> list[Invitation]:
        return self._repo.list_all()

    def get_admin_invitation(self, invitation_id: str) -> Invitation:
        inv = self._repo.get_by_id(invitation_id)
        if inv is None:
            raise InvitationNotFoundError()
        return inv

    def revoke(self, invitation_id: str) -> Invitation:
        inv = self.get_admin_invitation(invitation_id)
        if inv.status == InvitationStatus.REVOKED:
            return inv
        if inv.status == InvitationStatus.CONSUMED:
            # 业务上可选择拒绝撤销已消费邀请，这里保持幂等：返回现状
            return inv
        updated = replace(inv, status=InvitationStatus.REVOKED)
        self._repo.save(updated)
        return updated

    def consume(self, *, invitation_id: str, user_id: str, email: str) -> Invitation:
        inv = self.get_admin_invitation(invitation_id)
        if inv.target_email.strip().lower() != email.strip().lower():
            raise InvitationEmailMismatchError()

        if inv.status == InvitationStatus.CONSUMED:
            return inv
        if inv.status == InvitationStatus.REVOKED:
            raise InvitationRevokedError()

        # expired 派生
        self._ensure_pending_valid(inv)

        now = _iso(_now_utc())
        updated = replace(
            inv,
            status=InvitationStatus.CONSUMED,
            consumed_at=now,
            consumed_by_user_id=user_id,
        )
        self._repo.save(updated)
        return updated

    def _ensure_pending_valid(self, inv: Invitation) -> None:
        if inv.status == InvitationStatus.REVOKED:
            raise InvitationRevokedError()
        if inv.status == InvitationStatus.CONSUMED:
            raise InvitationAlreadyConsumedError()
        # expired 派生
        try:
            expires = datetime.fromisoformat(inv.expires_at.replace("Z", "+00:00"))
        except ValueError:
            # 无法解析则视为已过期
            raise InvitationExpiredError()
        if _now_utc() > expires:
            raise InvitationExpiredError()

    def get_public_preview(self, token: str) -> Invitation:
        token_hash = sha256_hex(token)
        inv = self._repo.get_by_token_hash(token_hash)
        if inv is None:
            raise InvitationNotFoundError()
        self._ensure_pending_valid(inv)
        return inv

    def start(self, token: str) -> Invitation:
        inv = self.get_public_preview(token)
        return inv

    def build_authentik_redirect_url(self) -> str:
        # 首版为延迟创建模式：这里先返回一个可联调占位 URL。
        # 真正上线时应在此创建/换取 Authentik enrollment URL，并返回 itoken URL。
        base = (self._settings.authentik_public_url or "").rstrip("/")
        itoken = "stub"
        return f"{base}/if/flow/clawloops-invitation-enrollment/?itoken={itoken}"

