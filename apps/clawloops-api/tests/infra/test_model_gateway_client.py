from app.infra.model_gateway_client import ModelGatewayClient


def test_model_gateway_client_uses_bearer_header_when_api_key_present():
    client = ModelGatewayClient("http://litellm:4000", api_key="sk-local-master")

    assert client._headers() == {"Authorization": "Bearer sk-local-master"}


def test_model_gateway_client_omits_header_without_api_key():
    client = ModelGatewayClient("http://litellm:4000")

    assert client._headers() == {}
