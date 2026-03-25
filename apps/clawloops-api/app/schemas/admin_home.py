from __future__ import annotations

from pydantic import BaseModel

from app.schemas.invitations import AdminInvitationItem


class AdminHomeSummary(BaseModel):
    totalUsers: int
    activeUsers: int
    disabledUsers: int
    pendingInvitations: int
    expiringInvitations24h: int
    runningRuntimes: int
    runtimeErrors: int


class AdminHomeRuntimeAlert(BaseModel):
    userId: str
    runtimeId: str
    observedState: str
    lastError: str | None = None
    updatedAt: str | None = None


class AdminHomeAttention(BaseModel):
    pendingInvitations: list[AdminInvitationItem]
    runtimeAlerts: list[AdminHomeRuntimeAlert]


class AdminHomeResponse(BaseModel):
    summary: AdminHomeSummary
    attention: AdminHomeAttention

