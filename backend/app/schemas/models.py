from typing import Any

from pydantic import BaseModel


class ModelItem(BaseModel):
    model_id: str
    name: str
    provider: str | None = None
    source: str
    enabled: bool = True


class ModelListResponse(BaseModel):
    models: list[dict[str, Any]]


class ModelBindingItem(BaseModel):
    model_id: str
    credential_id: str | None = None
    source: str


class ModelBindingsResponse(BaseModel):
    bindings: list[ModelBindingItem]


class UpdateModelBindingRequest(BaseModel):
    credential_id: str | None = None

