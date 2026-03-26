from pydantic import BaseModel

from app.schemas.auth import SessionUser


class InvitationPreviewItem(BaseModel):
    invitationId: str | None = None
    targetEmail: str
    loginUsername: str | None = None
    workspaceId: str
    workspaceName: str
    role: str
    status: str
    expiresAt: str


class InvitationPreviewResponse(BaseModel):
    valid: bool
    invitation: InvitationPreviewItem | None = None


class InvitationAcceptRequest(BaseModel):
    username: str
    password: str
    passwordConfirm: str


class InvitationAcceptWorkspaceBinding(BaseModel):
    workspaceId: str
    workspaceName: str
    role: str


class InvitationAcceptResult(BaseModel):
    accepted: bool
    replayed: bool | None = None
    redirectTo: str | None = None
    user: SessionUser | None = None
    workspaceBinding: InvitationAcceptWorkspaceBinding | None = None

