from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import get_app_settings, get_auth_context, get_model_repository, require_active_user
from app.infra.model_gateway_client import ModelGatewayClient
from app.repositories.model_repository import ModelRepository
from app.schemas.models import ModelItem, ModelListResponse
from app.services.model_service import ModelService


router = APIRouter(tags=["models"], dependencies=[Depends(require_active_user)])


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    ctx: AuthContext = Depends(get_auth_context),
    settings=Depends(get_app_settings),
    model_repo: ModelRepository = Depends(get_model_repository),
) -> ModelListResponse:
    model_base_url = settings.model_gateway_base_url or "http://litellm:4000"
    service = ModelService(model_repo=model_repo)
    governed = service.filter_models_by_provider_readiness(
        service.list_models_for_user(ctx.userId),
        settings.is_provider_ready,
    )
    governed = service.prioritize_models(
        governed,
        settings.get_model_gateway_default_models(),
    )
    preferred_models = [m.model_id for m in governed]

    client = ModelGatewayClient(model_base_url, api_key=settings.litellm_api_key)
    service.ensure_openrouter_models_registered(
        governed,
        model_gateway_client=client,
        openrouter_base_url=settings.openrouter_base_url,
        openrouter_api_key=settings.provider_openrouter_api_key or settings.openrouter_api_key,
    )
    payload = client.get_user_model_config(user_id=ctx.userId, preferred_models=preferred_models)
    models = payload.get("models", []) if isinstance(payload, dict) else []
    if not isinstance(models, list):
        models = []

    return ModelListResponse(
        models=[
            ModelItem(
                modelId=model_id,
                name=next((m.name for m in governed if m.model_id == model_id), model_id),
                provider="litellm",
                source="gateway",
                pricingType=next((m.pricing_type.value for m in governed if m.model_id == model_id), None),
                enabled=True,
                defaultRoute=next(
                    (
                        m.default_route
                        for m in governed
                        if m.model_id == model_id and m.provider == "ollama" and m.default_route
                    ),
                    f"litellm/{model_id}",
                ),
            )
            for model_id in models
        ]
    )
