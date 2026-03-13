from app.domain.models import Model, ModelSource
from app.repositories.model_repository import InMemoryModelRepository
from app.services.model_service import ModelService


def test_model_service_list_models():
    model_repo = InMemoryModelRepository()
    service = ModelService(model_repo)

    models = service.list_models_for_user("u_001")
    assert models
    assert all(isinstance(m, Model) for m in models)
    assert {m.source for m in models} == {ModelSource.SHARED}
    assert all(m.user_visible is True for m in models)


def test_model_service_admin_update_affects_visibility():
    model_repo = InMemoryModelRepository()
    service = ModelService(model_repo)

    updated = service.update_model(
        "gpt-4-mini",
        enabled=False,
        user_visible=False,
        default_route="openai/alt-mini",
        default_provider_credential_id="pc_001",
    )
    assert updated.enabled is False
    assert updated.user_visible is False
    assert updated.default_route == "openai/alt-mini"
    assert updated.default_provider_credential_id == "pc_001"

    assert service.list_models_for_user("u_001") == []
    admin_models = service.list_models_for_admin()
    assert len(admin_models) == 1
    assert admin_models[0].model_id == "gpt-4-mini"

