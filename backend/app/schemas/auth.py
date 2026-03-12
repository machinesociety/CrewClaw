from pydantic import BaseModel


class AuthMeResponse(BaseModel):
    """
    对应 GET /api/v1/auth/me 的响应体。

    TODO: 根据实际 AuthContext 完善字段来源。
    """

    authenticated: bool
    user_id: str
    subject_id: str
    tenant_id: str
    role: str
    is_admin: bool
    is_disabled: bool


class AccessCheckResponse(BaseModel):
    """
    对应 GET /api/v1/auth/access 的响应体。
    """

    allowed: bool
    reason: str | None = None

