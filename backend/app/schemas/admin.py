from pydantic import BaseModel


class UpdateUserStatusRequest(BaseModel):
    status: str


class AdminUserRuntimeResponse(BaseModel):
    runtime_id: str
    desired_state: str
    observed_state: str
    browser_url: str | None = None
    internal_endpoint: str | None = None
    last_error: str | None = None


class AdminUserCredentialsResponse(BaseModel):
    credentials: list[dict]


class AdminUsageSummaryResponse(BaseModel):
    total_tokens: int
    used_tokens: int

