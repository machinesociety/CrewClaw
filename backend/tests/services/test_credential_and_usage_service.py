from app.domain.credentials import CredentialStatus
from app.repositories.model_repository import (
    InMemoryCredentialRepository,
    InMemoryUsageRepository,
)
from app.services.model_service import CredentialService, UsageService


def test_credential_service_crud_and_verify():
    repo = InMemoryCredentialRepository()
    service = CredentialService(credential_repo=repo)

    cred = service.create_credential("u_001", "default", "secret-key")
    assert cred.user_id == "u_001"
    assert cred.status == CredentialStatus.ACTIVE

    listed = service.list_credentials("u_001")
    assert len(listed) == 1

    verified = service.verify_credential("u_001", cred.credential_id)
    assert verified.status == CredentialStatus.ACTIVE
    assert verified.last_validated_at is not None

    service.delete_credential("u_001", cred.credential_id)
    assert service.list_credentials("u_001") == []


def test_usage_service_default_and_set():
    repo = InMemoryUsageRepository()
    service = UsageService(usage_repo=repo)

    summary = service.get_user_usage("u_001")
    assert summary.user_id == "u_001"
    assert summary.total_tokens == 0

    repo.set_user_usage(summary.__class__(user_id="u_001", total_tokens=1234))
    summary2 = service.get_user_usage("u_001")
    assert summary2.total_tokens == 1234

