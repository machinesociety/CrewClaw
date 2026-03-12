from pydantic import BaseModel


class SyncUserRequest(BaseModel):
    subject_id: str


class RuntimeBindingUpsertRequest(BaseModel):
    runtime_id: str
    volume_id: str
    image_ref: str
    desired_state: str
    observed_state: str
    browser_url: str | None = None
    internal_endpoint: str | None = None
    retention_policy: str
    last_error: str | None = None


class RuntimeBindingStateUpdateRequest(BaseModel):
    desired_state: str
    observed_state: str
    browser_url: str | None = None
    internal_endpoint: str | None = None
    last_error: str | None = None


class ModelConfigResponse(BaseModel):
    base_url: str
    models: list[str]
    gateway_access_token_ref: str
    config_render_version: str


class UsageRecordItem(BaseModel):
    """
    TODO: 根据 OpenClaw usage 上报格式补充字段。
    """

    user_id: str
    total_tokens: int


class EnsureContainerRequest(BaseModel):
    user_id: str
    runtime_id: str
    image_ref: str
    volume_id: str
    route_host: str
    config_file_path: str
    secret_file_path: str
    retention_policy: str


class ContainerStateResponse(BaseModel):
    runtime_id: str
    observed_state: str
    internal_endpoint: str | None = None
    message: str | None = None

