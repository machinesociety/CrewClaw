from pydantic import BaseModel


class UpdateUserStatusRequest(BaseModel):
    status: str


class AdminUserRuntimeResponse(BaseModel):
    runtimeId: str
    volumeId: str
    imageRef: str
    desiredState: str
    observedState: str
    browserUrl: str | None = None
    internalEndpoint: str | None = None
    retentionPolicy: str
    lastError: str | None = None


class AdminUserListItem(BaseModel):
    userId: str
    subjectId: str
    role: str
    status: str
    runtimeObservedState: str | None = None
    lastLoginAt: str | None = None


class AdminUserDetailResponse(BaseModel):
    userId: str
    subjectId: str
    tenantId: str
    role: str
    status: str
    createdAt: str | None = None
    updatedAt: str | None = None


class AdminUsageSummaryResponse(BaseModel):
    totalTokens: int
    usedTokens: int

