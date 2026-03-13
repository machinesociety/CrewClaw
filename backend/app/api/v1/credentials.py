from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import get_auth_context, require_active_user
from app.repositories.model_repository import (
    CredentialRepository,
    get_inmemory_credential_repository,
)
from app.schemas.credentials import (
    CredentialItem,
    CredentialListResponse,
    CreateCredentialRequest,
    VerifyCredentialResponse,
)
from app.services.model_service import CredentialService


router = APIRouter(tags=["credentials"], dependencies=[Depends(require_active_user)])


def get_credential_repository() -> CredentialRepository:
    return get_inmemory_credential_repository()


def get_credential_service(
    repo: CredentialRepository = Depends(get_credential_repository),
) -> CredentialService:
    return CredentialService(credential_repo=repo)


@router.get("/credentials", response_model=CredentialListResponse)
async def list_credentials(
    ctx: AuthContext = Depends(get_auth_context),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialListResponse:
    """
    获取当前用户凭据列表（仅元数据，不含明文）。
    """
    items = service.list_credentials(ctx.userId)
    return CredentialListResponse(
        credentials=[
            CredentialItem(
                credential_id=c.credential_id,
                name=c.name,
                status=c.status.value,
                last_validated_at=c.last_validated_at,
            )
            for c in items
        ]
    )


@router.post("/credentials", response_model=CredentialItem, status_code=201)
async def create_credential(
    body: CreateCredentialRequest,
    ctx: AuthContext = Depends(get_auth_context),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialItem:
    """
    新增用户凭据。
    """
    cred = service.create_credential(ctx.userId, body.name, body.secret)
    return CredentialItem(
        credential_id=cred.credential_id,
        name=cred.name,
        status=cred.status.value,
        last_validated_at=cred.last_validated_at,
    )


@router.post("/credentials/{credential_id}/verify", response_model=VerifyCredentialResponse)
async def verify_credential(
    credential_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    service: CredentialService = Depends(get_credential_service),
) -> VerifyCredentialResponse:
    """
    验证用户凭据。
    """
    cred = service.verify_credential(ctx.userId, credential_id)
    return VerifyCredentialResponse(
        verified=cred.status == CredentialStatus.ACTIVE,
        status=cred.status.value,
        last_validated_at=cred.last_validated_at,
    )


@router.delete("/credentials/{credential_id}", status_code=204)
async def delete_credential(
    credential_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    service: CredentialService = Depends(get_credential_service),
) -> None:
    """
    删除用户凭据。
    """
    service.delete_credential(ctx.userId, credential_id)
    return None

