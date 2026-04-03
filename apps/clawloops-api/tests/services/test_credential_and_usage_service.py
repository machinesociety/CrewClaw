from app.domain.credentials import ProviderCredentialStatus
from app.domain.models import UsageSummary
from app.repositories.model_repository import (
    InMemoryProviderCredentialRepository,
    InMemoryUsageRepository,
)
from app.services.model_service import ProviderCredentialService, UsageService


def test_provider_credential_service_crud_and_verify():
    repo = InMemoryProviderCredentialRepository()
    service = ProviderCredentialService(credential_repo=repo)

    cred = service.create_credential("openai", "default", "secret-key")
    assert cred.provider == "openai"
    assert cred.status == ProviderCredentialStatus.ACTIVE

    listed = service.list_credentials()
    assert len(listed) == 1

    verified = service.verify_credential(cred.credential_id)
    assert verified.status == ProviderCredentialStatus.ACTIVE
    assert verified.last_validated_at is not None

    service.delete_credential(cred.credential_id)
    assert service.list_credentials() == []


def test_usage_service_default_set_and_total():
    repo = InMemoryUsageRepository()
    service = UsageService(usage_repo=repo)

    summary = service.get_user_usage("u_001")
    assert summary.user_id == "u_001"
    assert summary.total_tokens == 0
    assert summary.used_tokens == 0

    repo.set_user_usage(UsageSummary(user_id="u_001", total_tokens=1234, used_tokens=1200))
    repo.set_user_usage(UsageSummary(user_id="u_002", total_tokens=200, used_tokens=180))
    summary2 = service.get_user_usage("u_001")
    assert summary2.total_tokens == 1234
    assert summary2.used_tokens == 1200

    total = service.get_total_usage()
    assert total.total_tokens == 1434
    assert total.used_tokens == 1380

