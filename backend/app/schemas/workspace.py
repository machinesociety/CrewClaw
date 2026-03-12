from pydantic import BaseModel


class WorkspaceEntryResponse(BaseModel):
    ready: bool
    runtime_id: str | None = None
    browser_url: str | None = None
    reason: str | None = None

