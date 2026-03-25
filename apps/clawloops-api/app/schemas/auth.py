from pydantic import BaseModel


class AuthInfo(BaseModel):
    provider: str
    method: str


class SessionUser(BaseModel):
    userId: str
    subjectId: str
    tenantId: str
    role: str
    status: str
    auth: AuthInfo
    isAdmin: bool
    isDisabled: bool


class AuthMeResponse(BaseModel):
    """对应 GET /api/v1/auth/me 的响应体。"""

    authenticated: bool
    user: SessionUser | None = None


class AccessCheckResponse(BaseModel):
    """对应 GET /api/v1/auth/access 的响应体。"""

    allowed: bool
    reason: str | None = None


class AuthOption(BaseModel):
    type: str
    enabled: bool
    label: str


class AuthOptionsResponse(BaseModel):
    provider: str
    methods: list[AuthOption]

