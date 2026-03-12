from pydantic import BaseModel


class CredentialItem(BaseModel):
    credential_id: str
    name: str
    status: str
    last_validated_at: str | None = None


class CredentialListResponse(BaseModel):
    credentials: list[CredentialItem]


class CreateCredentialRequest(BaseModel):
    name: str
    secret: str


class VerifyCredentialResponse(BaseModel):
    verified: bool
    status: str
    last_validated_at: str | None = None

