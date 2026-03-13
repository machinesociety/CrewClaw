from app.domain.credentials import Credential, CredentialStatus
from app.domain.models import BindingSource, Model, ModelSource
from app.repositories.model_repository import (
    InMemoryCredentialRepository,
    InMemoryModelBindingRepository,
    InMemoryModelRepository,
)
from app.services.model_service import CredentialService, ModelService, UsageService


def test_model_service_list_models():
    model_repo = InMemoryModelRepository()
    binding_repo = InMemoryModelBindingRepository()
    cred_repo = InMemoryCredentialRepository()
    service = ModelService(model_repo, binding_repo, cred_repo)

    models = service.list_models_for_user("u_001")
    assert models
    assert all(isinstance(m, Model) for m in models)
    assert {m.source for m in models} == {ModelSource.SHARED}


def test_model_service_update_binding_and_list():
    model_repo = InMemoryModelRepository()
    binding_repo = InMemoryModelBindingRepository()
    cred_repo = InMemoryCredentialRepository()

    # 先准备一个凭据
    cred = Credential(
        credential_id="cred_001",
        user_id="u_001",
        name="default-openai",
        status=CredentialStatus.ACTIVE,
        last_validated_at=None,
    )
    cred_repo.save(cred)

    service = ModelService(model_repo, binding_repo, cred_repo)

    binding = service.update_binding("u_001", "gpt-4-mini", "cred_001")
    assert binding.user_id == "u_001"
    assert binding.model_id == "gpt-4-mini"
    assert binding.credential_id == "cred_001"
    assert binding.source == BindingSource.USER_OWNED

    bindings = service.list_bindings_for_user("u_001")
    assert len(bindings) == 1
    assert bindings[0].model_id == "gpt-4-mini"

