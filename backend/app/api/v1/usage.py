from fastapi import APIRouter, Depends

from app.core.auth import AuthContext
from app.core.dependencies import get_auth_context, require_active_user
from app.repositories.model_repository import (
    UsageRepository,
    get_inmemory_usage_repository,
)
from app.schemas.usage import UsageSummaryResponse
from app.services.model_service import UsageService


router = APIRouter(tags=["usage"], dependencies=[Depends(require_active_user)])


def get_usage_repository() -> UsageRepository:
    return get_inmemory_usage_repository()


def get_usage_service(
    repo: UsageRepository = Depends(get_usage_repository),
) -> UsageService:
    return UsageService(usage_repo=repo)


@router.get("/usage/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    ctx: AuthContext = Depends(get_auth_context),
    service: UsageService = Depends(get_usage_service),
) -> UsageSummaryResponse:
    """
    获取当前用户用量摘要。
    """
    summary = service.get_user_usage(ctx.userId)
    return UsageSummaryResponse(
        user_id=summary.user_id,
        total_tokens=summary.total_tokens,
        used_tokens=summary.total_tokens,
    )

