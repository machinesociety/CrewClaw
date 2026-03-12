from dataclasses import dataclass
from enum import Enum


class CredentialStatus(str, Enum):
    ACTIVE = "active"
    INVALID = "invalid"
    DISABLED = "disabled"


@dataclass
class Credential:
    """
    用户凭据元数据（不包含明文 secret）。

    TODO:
    - secret 部分仅存储在专用 secret store 中，由其它组件管理。
    """

    credential_id: str
    user_id: str
    name: str
    status: CredentialStatus
    last_validated_at: str | None = None

