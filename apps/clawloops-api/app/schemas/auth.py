from pydantic import BaseModel


class SessionAuthInfo(BaseModel):
    provider: str
    method: str


class SessionUser(BaseModel):
    userId: str
    subjectId: str
    username: str | None = None
    tenantId: str
    role: str
    status: str
    auth: SessionAuthInfo
    isAdmin: bool
    isDisabled: bool
    mustChangePassword: bool | None = None
    passwordChangeReason: str | None = None


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
    enabled: bool | None = None
    label: str


class PasswordPolicy(BaseModel):
    minLength: int
    maxLength: int
    requireLetter: bool
    requireNumber: bool
    disallowUsernameAsPassword: bool
    disallowDefaultAdminPassword: bool | None = None


class AuthFeatures(BaseModel):
    forcedPasswordChange: bool | None = None
    passwordRecovery: bool | None = None
    thirdPartyLogin: bool | None = None


class AuthOptionsResponse(BaseModel):
    provider: str
    methods: list[AuthOption]
    passwordPolicy: PasswordPolicy | None = None
    features: AuthFeatures | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResult(BaseModel):
    redirectTo: str | None = None
    mustChangePassword: bool | None = None
    user: SessionUser | None = None


class LogoutResult(BaseModel):
    ok: bool


class PasswordChangeRequest(BaseModel):
    currentPassword: str
    newPassword: str
    newPasswordConfirm: str


class PasswordChangeResult(BaseModel):
    changed: bool
    redirectTo: str | None = None
    user: SessionUser | None = None

