from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True, slots=True)
class NewSession:
    token: str
    token_hash: str
    issued_at: datetime
    expires_at: datetime


def create_session(*, ttl_seconds: int) -> NewSession:
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return NewSession(
        token=token,
        token_hash=token_hash,
        issued_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
    )


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

