from pydantic import BaseModel


class SyncUserRequest(BaseModel):
    subjectId: str


class RuntimeBindingUpsertRequest(BaseModel):
    runtimeId: str
    volumeId: str
    imageRef: str
    desiredState: str
    observedState: str
    browserUrl: str | None = None
    internalEndpoint: str | None = None
    retentionPolicy: str
    lastError: str | None = None


class RuntimeBindingStateUpdateRequest(BaseModel):
    desiredState: str
    observedState: str
    browserUrl: str | None = None
    internalEndpoint: str | None = None
    lastError: str | None = None


class ModelConfigResponse(BaseModel):
    baseUrl: str
    models: list[str]
    gatewayAccessTokenRef: str
    configRenderVersion: str


class UsageRecordItem(BaseModel):
    """
    TODO: 根据 OpenClaw usage 上报格式补充字段。
    """

    userId: str
    totalTokens: int


class ConfigMount(BaseModel):
    configFilePath: str
    secretFilePath: str


class EnsureContainerRequest(BaseModel):
    userId: str
    runtimeId: str
    imageRef: str
    volumeId: str
    routeHost: str
    configMount: ConfigMount
    retentionPolicy: str


class ContainerStateResponse(BaseModel):
    runtimeId: str
    observedState: str
    internalEndpoint: str | None = None
    message: str | None = None

