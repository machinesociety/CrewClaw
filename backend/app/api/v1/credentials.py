from fastapi import APIRouter

from app.schemas.credentials import (
    CredentialItem,
    CredentialListResponse,
    CreateCredentialRequest,
    VerifyCredentialResponse,
)


router = APIRouter(tags=["credentials"])


@router.get("/credentials", response_model=CredentialListResponse)
async def list_credentials() -> CredentialListResponse:
    """
    获取当前用户凭据列表（仅元数据，不含明文）。

    TODO:
    - 从 Credential 仓储中查询真实数据。
    """
    return CredentialListResponse(
        credentials=[
            CredentialItem(
                credential_id="cred_001",
                name="default-openai",
                status="active",
                last_validated_at=None,
            )
        ]
    )


@router.post("/credentials", response_model=CredentialItem, status_code=201)
async def create_credential(body: CreateCredentialRequest) -> CredentialItem:
    """
    新增用户凭据。

    TODO:
    - 将 secret 写入专用 secret store。
    - 在仓储中保存凭据元数据。
    """
    _ = body
    return CredentialItem(
        credential_id="cred_new",
        name="new-credential",
        status="active",
        last_validated_at=None,
    )


@router.post("/credentials/{credential_id}/verify", response_model=VerifyCredentialResponse)
async def verify_credential(credential_id: str) -> VerifyCredentialResponse:
    """
    验证用户凭据。

    TODO:
    - 调用模型网关或 provider 执行真实校验。
    """
    _ = credential_id
    return VerifyCredentialResponse(verified=True, status="active", last_validated_at="2026-01-01T00:00:00Z")


@router.delete("/credentials/{credential_id}", status_code=204)
async def delete_credential(credential_id: str) -> None:
    """
    删除用户凭据。

    TODO:
    - 在仓储和 secret store 中删除或标记失效。
    """
    _ = credential_id
    return None

