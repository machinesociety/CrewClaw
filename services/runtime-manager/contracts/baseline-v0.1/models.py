from pydantic import BaseModel, Field, HttpUrl, field_validator

from runtime_manager.constants.baseline import DEFAULT_BRIDGE_PORT, DEFAULT_GATEWAY_PORT
from contracts.enums import ObservedState, RetentionPolicy


class ConfigMount(BaseModel):
    config_file_path: str = Field(..., min_length=1)
    secret_file_path: str = Field(..., min_length=1)


class CompatConfig(BaseModel):
    openclaw_config_dir: str = Field(..., min_length=1)
    openclaw_workspace_dir: str = Field(..., min_length=1)
    network_name: str = Field(..., min_length=1)
    gateway_port: int = Field(default=DEFAULT_GATEWAY_PORT)
    bridge_port: int = Field(default=DEFAULT_BRIDGE_PORT)

    @field_validator("gateway_port", "bridge_port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("port must be in range 1-65535")
        return value


class EnsureRunningRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    runtime_id: str = Field(..., min_length=1)
    image_ref: str = Field(..., min_length=1)
    volume_id: str = Field(..., min_length=1)
    route_host: str = Field(..., min_length=1)
    config_mount: ConfigMount
    retention_policy: RetentionPolicy
    compat: CompatConfig


class EnsureRunningResponse(BaseModel):
    runtime_id: str = Field(..., min_length=1)
    observed_state: ObservedState
    internal_endpoint: HttpUrl
    message: str = Field(..., min_length=1)


class StopRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    runtime_id: str = Field(..., min_length=1)


class StopResponse(BaseModel):
    runtime_id: str = Field(..., min_length=1)
    observed_state: ObservedState = Field(default=ObservedState.STOPPED)
    message: str = Field(..., min_length=1)


class DeleteRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    runtime_id: str = Field(..., min_length=1)
    retention_policy: RetentionPolicy


class DeleteResponse(BaseModel):
    runtime_id: str = Field(..., min_length=1)
    observed_state: ObservedState = Field(default=ObservedState.DELETED)
    message: str = Field(..., min_length=1)


class RuntimeStatusResponse(BaseModel):
    runtime_id: str = Field(..., min_length=1)
    observed_state: ObservedState
    internal_endpoint: HttpUrl | None = None
    message: str = Field(..., min_length=1)

