from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import get_auth_context, require_active_user
from app.repositories.model_repository import ModelRepository, get_inmemory_model_repository
from app.schemas.models import ModelItem, ModelListResponse
from app.services.model_service import ModelService


router = APIRouter(tags=["models"], dependencies=[Depends(require_active_user)])


def get_model_repository() -> ModelRepository:
    return get_inmemory_model_repository()


def get_model_service(
    model_repo: ModelRepository = Depends(get_model_repository),
) -> ModelService:
    return ModelService(model_repo=model_repo)


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    ctx: AuthContext = Depends(get_auth_context),
    service: ModelService = Depends(get_model_service),
) -> ModelListResponse:
    models = service.list_models_for_user(ctx.userId)
    return ModelListResponse(
        models=[
            ModelItem(
                modelId=m.model_id,
                name=m.name,
                provider=m.provider,
                source=m.source.value,
                enabled=m.enabled,
                defaultRoute=m.default_route,
            )
            for m in models
        ]
    )

