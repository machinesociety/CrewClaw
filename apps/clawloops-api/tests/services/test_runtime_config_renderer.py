from app.domain.runtime_ports import ModelConfig
from app.schemas.runtime import DesiredState, ObservedState, RetentionPolicy, RuntimeBindingSnapshot
from app.services.runtime_config_renderer import RuntimeConfigRenderer


def test_runtime_config_renderer_disables_device_pairing():
    renderer = RuntimeConfigRenderer()
    binding = RuntimeBindingSnapshot(
        runtimeId="rt_001",
        volumeId="vol_001",
        imageRef="clawloops-runtime-wrapper:openclaw-1.0.0",
        desiredState=DesiredState.running,
        observedState=ObservedState.creating,
        browserUrl=None,
        internalEndpoint=None,
        retentionPolicy=RetentionPolicy.preserve_workspace,
        lastError=None,
    )
    model = ModelConfig(
        base_url="http://litellm:4000",
        models=["qwen-max-proxy"],
        model_pricing={"qwen-max-proxy": "free"},
        config_render_version="v1",
        gateway_access_token_ref="token_ref_001",
    )

    openclaw_json, _ = renderer.render("u_001", binding, model)
    control_ui = openclaw_json["gateway"]["controlUi"]
    assert control_ui["dangerouslyDisableDeviceAuth"] is True


def test_runtime_config_renderer_uses_injected_litellm_api_key():
    renderer = RuntimeConfigRenderer(litellm_api_key="sk-local-master")
    binding = RuntimeBindingSnapshot(
        runtimeId="rt_001",
        volumeId="vol_001",
        imageRef="clawloops-runtime-wrapper:openclaw-1.0.0",
        desiredState=DesiredState.running,
        observedState=ObservedState.creating,
        browserUrl=None,
        internalEndpoint=None,
        retentionPolicy=RetentionPolicy.preserve_workspace,
        lastError=None,
    )
    model = ModelConfig(
        base_url="http://litellm:4000",
        models=["qwen-max-proxy"],
        model_pricing={"qwen-max-proxy": "free"},
        config_render_version="v1",
        gateway_access_token_ref="token_ref_001",
    )
    openclaw_json, _ = renderer.render("u_001", binding, model)
    assert openclaw_json["models"]["providers"]["litellm"]["apiKey"] == "sk-local-master"
    assert list(openclaw_json["agents"]["defaults"]["models"]) == ["litellm/qwen-max-proxy"]


def test_runtime_config_renderer_uses_native_ollama_provider_for_local_models():
    renderer = RuntimeConfigRenderer(
        litellm_api_key="sk-local-master",
        ollama_base_url="http://ollama:11434",
    )
    binding = RuntimeBindingSnapshot(
        runtimeId="rt_001",
        volumeId="vol_001",
        imageRef="clawloops-runtime-wrapper:openclaw-1.0.0",
        desiredState=DesiredState.running,
        observedState=ObservedState.creating,
        browserUrl=None,
        internalEndpoint=None,
        retentionPolicy=RetentionPolicy.preserve_workspace,
        lastError=None,
    )
    model = ModelConfig(
        base_url="http://litellm:4000",
        models=["ollama-qwen2.5-7b-free", "qwen-max-proxy"],
        model_pricing={
            "ollama-qwen2.5-7b-free": "free",
            "qwen-max-proxy": "free",
        },
        model_routes={
            "ollama-qwen2.5-7b-free": "ollama/qwen2.5:7b",
            "qwen-max-proxy": "litellm/qwen-max-proxy",
        },
        config_render_version="v1",
        gateway_access_token_ref="token_ref_001",
    )

    openclaw_json, _ = renderer.render("u_001", binding, model)

    assert openclaw_json["models"]["providers"]["ollama"]["api"] == "ollama"
    assert openclaw_json["models"]["providers"]["ollama"]["baseUrl"] == "http://ollama:11434"
    assert openclaw_json["models"]["providers"]["ollama"]["models"][0]["id"] == "qwen2.5:7b"
    assert "ollama/qwen2.5:7b" in openclaw_json["agents"]["defaults"]["models"]
    assert "litellm/qwen-max-proxy" in openclaw_json["agents"]["defaults"]["models"]
    assert openclaw_json["agents"]["defaults"]["model"]["primary"] == "ollama/qwen2.5:7b"
