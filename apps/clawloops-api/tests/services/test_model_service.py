from app.domain.models import Model, ModelSource, PricingType
from app.repositories.model_repository import InMemoryModelRepository
from app.services.model_service import ModelService, build_openrouter_safe_model_id


def test_model_service_list_models():
    model_repo = InMemoryModelRepository()
    service = ModelService(model_repo)

    models = service.list_models_for_user("u_001")
    assert models
    assert all(isinstance(m, Model) for m in models)
    assert {m.source for m in models} == {ModelSource.SHARED}
    assert all(m.user_visible is True for m in models)
    assert {m.model_id for m in models} == {
        "ollama-qwen2.5-7b-free",
        "qwen-max-proxy",
        "gpt-4-mini-paid",
    }


def test_model_service_admin_update_affects_visibility():
    model_repo = InMemoryModelRepository()
    service = ModelService(model_repo)

    updated = service.update_model(
        "gpt-4-mini-paid",
        enabled=False,
        user_visible=False,
        pricing_type=PricingType.FREE,
        default_route="openrouter/alt-mini",
        default_provider_credential_id="pc_001",
    )
    assert updated.enabled is False
    assert updated.user_visible is False
    assert updated.pricing_type == PricingType.FREE
    assert updated.default_route == "openrouter/alt-mini"
    assert updated.default_provider_credential_id == "pc_001"

    user_models = service.list_models_for_user("u_001")
    assert len(user_models) == 2
    assert {model.model_id for model in user_models} == {
        "ollama-qwen2.5-7b-free",
        "qwen-max-proxy",
    }
    admin_models = service.list_models_for_admin()
    assert len(admin_models) == 3
    assert {m.model_id for m in admin_models} == {
        "ollama-qwen2.5-7b-free",
        "qwen-max-proxy",
        "gpt-4-mini-paid",
    }


def test_prioritize_models_respects_preferred_default_order():
    service = ModelService(InMemoryModelRepository())
    models = [
        Model(
            model_id="gpt-4-mini-paid",
            name="GPT-4 Mini",
            provider="openrouter",
            source=ModelSource.SHARED,
            pricing_type=PricingType.PAID,
            enabled=True,
            user_visible=True,
            default_route="openrouter/openai/gpt-4o-mini",
            default_provider_credential_id=None,
        ),
        Model(
            model_id="qwen-max-proxy",
            name="通义 Qwen Max（免费）",
            provider="dashscope",
            source=ModelSource.SHARED,
            pricing_type=PricingType.FREE,
            enabled=True,
            user_visible=True,
            default_route="litellm/qwen-max-proxy",
            default_provider_credential_id=None,
        ),
    ]

    prioritized = service.prioritize_models(models, ["qwen-max-proxy"])

    assert [model.model_id for model in prioritized] == [
        "qwen-max-proxy",
        "gpt-4-mini-paid",
    ]


def test_filter_models_by_provider_readiness_excludes_unready_provider():
    service = ModelService(InMemoryModelRepository())
    models = [
        Model(
            model_id="qwen-max-proxy",
            name="通义 Qwen Max（免费）",
            provider="dashscope",
            source=ModelSource.SHARED,
            pricing_type=PricingType.FREE,
            enabled=True,
            user_visible=True,
            default_route="litellm/qwen-max-proxy",
            default_provider_credential_id=None,
        ),
        Model(
            model_id="ollama-qwen2.5-7b-free",
            name="Qwen 2.5 7B",
            provider="ollama",
            source=ModelSource.SHARED,
            pricing_type=PricingType.FREE,
            enabled=True,
            user_visible=True,
            default_route="ollama/qwen2.5:7b",
            default_provider_credential_id=None,
        ),
    ]

    filtered = service.filter_models_by_provider_readiness(
        models,
        lambda provider: provider != "dashscope",
    )

    assert [model.model_id for model in filtered] == ["ollama-qwen2.5-7b-free"]


def test_build_openrouter_safe_model_id_sanitizes_special_chars():
    assert (
        build_openrouter_safe_model_id("z-ai/glm-4.5-air:free")
        == "openrouter-z-ai-glm-4-5-air-free"
    )
    assert (
        build_openrouter_safe_model_id("google/gemma-3-27b-it:free")
        == "openrouter-google-gemma-3-27b-it-free"
    )


def test_sync_openrouter_models_uses_safe_alias_for_glm_free(monkeypatch):
    class _FakeEntry:
        def __init__(self, model_id: str, name: str):
            self.model_id = model_id
            self.name = name

    class _FakeClient:
        def __init__(self, base_url: str, api_key: str | None = None) -> None:
            _ = (base_url, api_key)

        def list_models(self):
            return [_FakeEntry("z-ai/glm-4.5-air:free", "Z.ai: GLM 4.5 Air (free)")]

    monkeypatch.setattr("app.services.model_service.OpenRouterClient", _FakeClient)

    model_repo = InMemoryModelRepository()
    service = ModelService(model_repo)

    stats = service.sync_openrouter_models(
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_api_key="sk-or-test",
    )

    synced = model_repo.get_model("openrouter-z-ai-glm-4-5-air-free")
    assert stats == {"fetched": 1, "created": 1, "updated": 0}
    assert synced is not None
    assert synced.name == "Z.ai: GLM 4.5 Air (free)"
    assert synced.provider == "openrouter"
    assert synced.pricing_type == PricingType.FREE
    assert synced.default_route == "litellm/openrouter-z-ai-glm-4-5-air-free"
    assert synced.upstream_model_id == "z-ai/glm-4.5-air:free"


def test_resolve_openrouter_upstream_model_id_uses_existing_safe_alias(monkeypatch):
    class _FakeEntry:
        def __init__(self, model_id: str, name: str):
            self.model_id = model_id
            self.name = name

    class _FakeClient:
        def __init__(self, base_url: str, api_key: str | None = None) -> None:
            _ = (base_url, api_key)

        def list_models(self):
            return [_FakeEntry("z-ai/glm-4.5-air:free", "Z.ai: GLM 4.5 Air (free)")]

    monkeypatch.setattr("app.services.model_service.OpenRouterClient", _FakeClient)

    model_repo = InMemoryModelRepository()
    service = ModelService(model_repo)
    model = Model(
        model_id="openrouter-z-ai-glm-4-5-air-free",
        name="Z.ai: GLM 4.5 Air (free)",
        provider="openrouter",
        source=ModelSource.SHARED,
        pricing_type=PricingType.FREE,
        enabled=True,
        user_visible=True,
        default_route="litellm/openrouter-z-ai-glm-4-5-air-free",
        default_provider_credential_id=None,
    )
    model_repo.save(model)

    resolved = service.resolve_openrouter_upstream_model_id(
        model,
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_api_key="sk-or-test",
    )

    assert resolved == "z-ai/glm-4.5-air:free"
    persisted = model_repo.get_model("openrouter-z-ai-glm-4-5-air-free")
    assert persisted is not None
    assert persisted.upstream_model_id == "z-ai/glm-4.5-air:free"
