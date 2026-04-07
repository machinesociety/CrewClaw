from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import get_app_settings, get_auth_context, require_active_user
from app.domain.models import Model, ModelSource
from app.infra.model_gateway_client import ModelGatewayClient
from app.repositories.model_repository import ModelRepository, get_inmemory_model_repository
from app.schemas.models import ModelItem, ModelListResponse
from app.services.model_service import ModelService


router = APIRouter(tags=["models"], dependencies=[Depends(require_active_user)])


def get_model_service(model_repo: ModelRepository = Depends(get_inmemory_model_repository)) -> ModelService:
    return ModelService(model_repo=model_repo)


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    ctx: AuthContext = Depends(get_auth_context),
    settings=Depends(get_app_settings),
    model_repo: ModelRepository = Depends(get_inmemory_model_repository),
    service: ModelService = Depends(get_model_service),
) -> ModelListResponse:
    model_base_url = settings.model_gateway_base_url or "http://litellm:4000"
    client = ModelGatewayClient(model_base_url, api_key=settings.litellm_api_key)

    available_model_ids: list[str] = []
    try:
        available_model_ids = client.list_models()
    except Exception:
        available_model_ids = []

    models: list[Model] = []
    if available_model_ids:
        for model_id in available_model_ids:
            if model_repo.get_model(model_id) is None:
                model_repo.save(
                    Model(
                        model_id=model_id,
                        name=model_id,
                        provider="litellm",
                        source=ModelSource.SHARED,
                        enabled=True,
                        user_visible=True,
                        default_route=f"litellm/{model_id}",
                        default_provider_credential_id=None,
                    )
                )
        for model_id in available_model_ids:
            m = model_repo.get_model(model_id)
            if m is not None and m.enabled and m.user_visible:
                models.append(m)
    else:
        models = service.list_models_for_user(ctx.userId)
        if not models:
            preferred_models = settings.get_model_gateway_default_models()
            for model_id in preferred_models:
                if model_repo.get_model(model_id) is None:
                    model_repo.save(
                        Model(
                            model_id=model_id,
                            name=model_id,
                            provider="litellm",
                            source=ModelSource.SHARED,
                            enabled=True,
                            user_visible=True,
                            default_route=f"litellm/{model_id}",
                            default_provider_credential_id=None,
                        )
                    )
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
