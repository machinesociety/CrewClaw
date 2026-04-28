from app.infra.model_gateway_client import ModelGatewayClient


def test_model_gateway_client_uses_bearer_header_when_api_key_present():
    client = ModelGatewayClient("http://litellm:4000", api_key="sk-local-master")

    assert client._headers() == {"Authorization": "Bearer sk-local-master"}


def test_model_gateway_client_omits_header_without_api_key():
    client = ModelGatewayClient("http://litellm:4000")

    assert client._headers() == {}


def test_model_gateway_client_get_user_model_config_intersects_with_gateway_models(monkeypatch):
    client = ModelGatewayClient("http://litellm:4000", api_key="sk-local-master")
    monkeypatch.setattr(
        client,
        "list_models",
        lambda: ["qwen-max-proxy", "gpt-4-mini-paid", "qwen-max-proxy"],
    )

    payload = client.get_user_model_config(
        user_id="u_001",
        preferred_models=["qwen-max-proxy", "openrouter-glm-4.5-air-free", "gpt-4-mini-paid"],
    )

    assert payload["models"] == ["qwen-max-proxy", "gpt-4-mini-paid"]


def test_model_gateway_client_get_user_model_config_falls_back_when_gateway_unavailable(monkeypatch):
    client = ModelGatewayClient("http://litellm:4000", api_key="sk-local-master")

    def _raise() -> list[str]:
        raise RuntimeError("gateway unavailable")

    monkeypatch.setattr(client, "list_models", _raise)

    payload = client.get_user_model_config(
        user_id="u_001",
        preferred_models=["qwen-max-proxy", "qwen-max-proxy", "gpt-4-mini-paid"],
    )

    assert payload["models"] == ["qwen-max-proxy", "gpt-4-mini-paid"]
