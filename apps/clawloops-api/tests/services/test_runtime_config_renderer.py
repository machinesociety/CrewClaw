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
        models=["gpt-4-mini"],
        gateway_access_token_ref="token_ref_001",
        config_render_version="v1",
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
        models=["gpt-4-mini"],
        gateway_access_token_ref="token_ref_001",
        config_render_version="v1",
    )
    openclaw_json, _ = renderer.render("u_001", binding, model)
    assert openclaw_json["models"]["providers"]["litellm"]["apiKey"] == "sk-local-master"
