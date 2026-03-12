from fastapi import APIRouter

from app.schemas.models import ModelListResponse, ModelBindingsResponse, UpdateModelBindingRequest


router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """
    获取当前用户可见模型列表。

    TODO:
    - 调用 ModelService 获取真实模型列表与来源。
    """
    return ModelListResponse(
        models=[
            {
                "model_id": "gpt-4-mini",
                "name": "GPT-4 Mini",
                "provider": "openai",
                "source": "shared",
                "enabled": True,
            }
        ]
    )


@router.get("/models/bindings", response_model=ModelBindingsResponse)
async def get_model_bindings() -> ModelBindingsResponse:
    """
    获取当前用户模型绑定关系。

    TODO:
    - 从 ModelBinding 仓储中查询绑定。
    """
    return ModelBindingsResponse(bindings=[])


@router.put("/models/{model_id}/binding", response_model=ModelBindingsResponse)
async def update_model_binding(model_id: str, body: UpdateModelBindingRequest) -> ModelBindingsResponse:
    """
    设置某模型的凭据绑定。

    TODO:
    - 调用 ModelService 更新绑定并返回最新绑定列表。
    """
    _ = (model_id, body)
    return ModelBindingsResponse(bindings=[])

