from __future__ import annotations

from pydantic import BaseModel


class InvitationPublicPreviewItem(BaseModel):
    targetEmail: str
    loginUsername: str | None = None
    workspaceId: str
    workspaceName: str | None = None
    role: str
    status: str
    expiresAt: str


class InvitationPublicPreviewResponse(BaseModel):
    valid: bool
    invitation: InvitationPublicPreviewItem | None = None


class PendingInvitationSession(BaseModel):
    ttlSeconds: int


class InvitationStartResponse(BaseModel):
    status: str
    pendingInvitationSession: PendingInvitationSession | None = None
    redirectUrl: str | None = None


class AdminInvitationItem(BaseModel):
    invitationId: str
    targetEmail: str
    loginUsername: str | None = None
    workspaceId: str
    role: str
    status: str
    expiresAt: str
    consumedAt: str | None = None
    consumedByUserId: str | None = None
    lastError: str | None = None
    createdAt: str | None = None


class AdminInvitationListResponse(BaseModel):
    invitations: list[AdminInvitationItem]


class CreateAdminInvitationRequest(BaseModel):
    targetEmail: str
    loginUsername: str | None = None
    workspaceId: str
    role: str
    expiresInHours: int

