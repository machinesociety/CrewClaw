from dataclasses import dataclass
from enum import Enum


class ModelSource(str, Enum):
    SHARED = "shared"
    LOCAL = "local"


class PricingType(str, Enum):
    FREE = "free"
    PAID = "paid"



@dataclass
class Model:
    """
    模型元数据。
    """

    model_id: str
    name: str
    provider: str | None
    source: ModelSource
    pricing_type: PricingType = PricingType.FREE
    enabled: bool = True
    user_visible: bool = True
    default_route: str | None = None
    default_provider_credential_id: str | None = None
    upstream_model_id: str | None = None


@dataclass
class UsageSummary:
    """
    用量摘要。

    TODO:
    - 与 OpenClaw 上报及网关日志的字段保持对齐。
    """

    user_id: str
    total_tokens: int
    used_tokens: int = 0
