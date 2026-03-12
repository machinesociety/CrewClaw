from fastapi import APIRouter

from app.schemas.usage import UsageSummaryResponse


router = APIRouter(tags=["usage"])


@router.get("/usage/summary", response_model=UsageSummaryResponse)
async def get_usage_summary() -> UsageSummaryResponse:
    """
    获取当前用户用量摘要。

    TODO:
    - 从 usage 仓储或网关统计中聚合真实数据。
    """
    return UsageSummaryResponse(
        user_id="u_001",
        total_tokens=1000000,
        used_tokens=12345,
    )

