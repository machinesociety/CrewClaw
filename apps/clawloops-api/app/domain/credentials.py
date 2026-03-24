from dataclasses import dataclass
from enum import Enum


class ProviderCredentialStatus(str, Enum):
    ACTIVE = "active"
    INVALID = "invalid"
    DISABLED = "disabled"


@dataclass
class ProviderCredential:
    """
    平台托管的 provider 凭据元数据。

    TODO:
    - secret 部分仅存储在专用 secret store 中，由其它组件管理。
    """

    credential_id: str
    provider: str
    name: str
    status: ProviderCredentialStatus
    last_validated_at: str | None = None

