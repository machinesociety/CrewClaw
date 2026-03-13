from fastapi import status

from app.core.dependencies import get_auth_context
from app.core.auth import AuthContext


def _auth_headers(subject: str = "authentik:user1") -> dict[str, str]:
    return {"X-Authentik-Subject": subject}


def test_models_list_and_bindings_empty(client):
    resp = client.get("/api/v1/models", headers=_auth_headers())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "models" in data
    assert data["models"]

    resp2 = client.get("/api/v1/models/bindings", headers=_auth_headers())
    assert resp2.status_code == status.HTTP_200_OK
    data2 = resp2.json()
    assert data2["bindings"] == []


def test_credentials_and_binding_flow(client):
    # 创建凭据
    resp_create = client.post(
        "/api/v1/credentials",
        headers=_auth_headers(),
        json={"name": "default-openai", "secret": "sk-..."},
    )
    assert resp_create.status_code == status.HTTP_201_CREATED
    cred = resp_create.json()

    # 列表中可见
    resp_list = client.get("/api/v1/credentials", headers=_auth_headers())
    assert resp_list.status_code == status.HTTP_200_OK
    creds = resp_list.json()["credentials"]
    assert any(c["credential_id"] == cred["credential_id"] for c in creds)

    # 绑定到模型
    resp_bind = client.put(
        "/api/v1/models/gpt-4-mini/binding",
        headers=_auth_headers(),
        json={"credential_id": cred["credential_id"]},
    )
    assert resp_bind.status_code == status.HTTP_200_OK
    bindings = resp_bind.json()["bindings"]
    assert any(
        b["model_id"] == "gpt-4-mini" and b["credential_id"] == cred["credential_id"]
        for b in bindings
    )

    # 用量摘要
    resp_usage = client.get("/api/v1/usage/summary", headers=_auth_headers())
    assert resp_usage.status_code == status.HTTP_200_OK
    usage = resp_usage.json()
    assert usage["user_id"]
    assert usage["total_tokens"] >= 0

