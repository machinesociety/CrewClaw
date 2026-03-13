from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import get_auth_context, require_active_user
from app.domain.models import ModelBinding
from app.repositories.model_repository import (
    CredentialRepository,
    ModelBindingRepository,
    ModelRepository,
    get_inmemory_credential_repository,
    get_inmemory_model_binding_repository,
    get_inmemory_model_repository,
)
from app.schemas.models import (
    ModelBindingsResponse,
    ModelItem,
    ModelListResponse,
    UpdateModelBindingRequest,
)
from app.services.model_service import ModelService


router = APIRouter(tags=["models"], dependencies=[Depends(require_active_user)])


def get_model_repository() -> ModelRepository:
    return get_inmemory_model_repository()


def get_model_binding_repository() -> ModelBindingRepository:
    return get_inmemory_model_binding_repository()


def get_credential_repository() -> CredentialRepository:
    return get_inmemory_credential_repository()


def get_model_service(
    model_repo: ModelRepository = Depends(get_model_repository),
    binding_repo: ModelBindingRepository = Depends(get_model_binding_repository),
    credential_repo: CredentialRepository = Depends(get_credential_repository),
) -> ModelService:
    return ModelService(
        model_repo=model_repo,
        binding_repo=binding_repo,
        credential_repo=credential_repo,
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    ctx: AuthContext = Depends(get_auth_context),
    service: ModelService = Depends(get_model_service),
) -> ModelListResponse:
    models = service.list_models_for_user(ctx.userId)
    return ModelListResponse(
        models=[
            {
                "model_id": m.model_id,
                "name": m.name,
                "provider": m.provider,
                "source": m.source.value,
                "enabled": m.enabled,
            }
            for m in models
        ]
    )


@router.get("/models/bindings", response_model=ModelBindingsResponse)
async def get_model_bindings(
    ctx: AuthContext = Depends(get_auth_context),
    service: ModelService = Depends(get_model_service),
) -> ModelBindingsResponse:
    bindings = service.list_bindings_for_user(ctx.userId)
    return ModelBindingsResponse(
        bindings=[
            {
                "model_id": b.model_id,
                "credential_id": b.credential_id,
                "source": b.source.value,
            }
            for b in bindings
        ]
    )


@router.put("/models/{model_id}/binding", response_model=ModelBindingsResponse)
async def update_model_binding(
    model_id: str,
    body: UpdateModelBindingRequest,
    ctx: AuthContext = Depends(get_auth_context),
    service: ModelService = Depends(get_model_service),
) -> ModelBindingsResponse:
    service.update_binding(ctx.userId, model_id, body.credential_id)
    bindings = service.list_bindings_for_user(ctx.userId)
    return ModelBindingsResponse(
        bindings=[
            {
                "model_id": b.model_id,
                "credential_id": b.credential_id,
                "source": b.source.value,
            }
            for b in bindings
        ]
    )

