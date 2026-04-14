from app.domain.models import Model, ModelSource, PricingType
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
            default_route="litellm/ollama-qwen2.5-7b-free",
            default_provider_credential_id=None,
        ),
    ]

    filtered = service.filter_models_by_provider_readiness(
        models,
        lambda provider: provider != "dashscope",
    )

    assert [model.model_id for model in filtered] == ["ollama-qwen2.5-7b-free"]
