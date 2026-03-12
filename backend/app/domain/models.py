from dataclasses import dataclass
from enum import Enum


class ModelSource(str, Enum):
    SHARED = "shared"
    LOCAL = "local"


@dataclass
class Model:
    """
    模型元数据。
    """

    model_id: str
    name: str
    provider: str | None
    source: ModelSource
    enabled: bool = True


class BindingSource(str, Enum):
    PLATFORM_DEFAULT = "platform_default"
    USER_OWNED = "user_owned"


@dataclass
class ModelBinding:
    """
    模型与凭据的绑定关系。
    """

    user_id: str
    model_id: str
    credential_id: str | None
    source: BindingSource


@dataclass
class UsageSummary:
    """
    用量摘要。

    TODO:
    - 与 OpenClaw 上报及网关日志的字段保持对齐。
    """

    user_id: str
    total_tokens: int

