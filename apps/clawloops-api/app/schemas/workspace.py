from pydantic import BaseModel



class WorkspaceEntryResponse(BaseModel):
    ready: bool
    hasWorkspace: bool
    runtimeId: str | None = None
    browserUrl: str | None = None
    reason: str | None = None

