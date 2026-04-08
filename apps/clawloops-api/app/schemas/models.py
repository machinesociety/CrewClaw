from pydantic import BaseModel
from typing import List, Optional


class ModelItem(BaseModel):
    modelId: str
    name: str
    provider: str
    source: str
    enabled: bool
    defaultRoute: str


class ModelListResponse(BaseModel):
    models: List[ModelItem]


class AdminModelItem(BaseModel):
    modelId: str
    name: str
    provider: str
    source: str
    enabled: bool
    defaultRoute: str


class AdminModelListResponse(BaseModel):
    models: List[AdminModelItem]


class UpdateAdminModelRequest(BaseModel):
    enabled: bool
