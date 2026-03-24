from pydantic import BaseModel


class ProviderCredentialItem(BaseModel):
    credentialId: str
    provider: str
    name: str
    status: str
    verified: bool
    lastValidatedAt: str | None = None


class ProviderCredentialListResponse(BaseModel):
    credentials: list[ProviderCredentialItem]


class CreateProviderCredentialRequest(BaseModel):
    provider: str
    name: str
    secret: str


class VerifyProviderCredentialResponse(BaseModel):
    verified: bool
    status: str
    lastValidatedAt: str | None = None

