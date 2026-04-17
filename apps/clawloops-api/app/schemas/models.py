from pydantic import BaseModel


class ModelItem(BaseModel):
    modelId: str
    name: str
    provider: str | None = None
    source: str
    pricingType: str | None = None
    enabled: bool = True
    defaultRoute: str | None = None


class ModelListResponse(BaseModel):
    models: list[ModelItem]


class AdminModelItem(ModelItem):
    userVisible: bool = True
    defaultProviderCredentialId: str | None = None
    runtimeRefreshTriggered: bool = False
    runtimeBrowserUrl: str | None = None


class AdminModelListResponse(BaseModel):
    models: list[AdminModelItem]


class UpdateAdminModelRequest(BaseModel):
    enabled: bool | None = None
    userVisible: bool | None = None
    pricingType: str | None = None
    defaultRoute: str | None = None
    defaultProviderCredentialId: str | None = None
