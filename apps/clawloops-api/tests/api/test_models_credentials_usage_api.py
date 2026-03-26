from fastapi import status
from app.core.dependencies import get_sqlalchemy_user_repository
from app.domain.users import User, UserRole, UserStatus
from app.repositories.model_repository import reset_inmemory_model_repositories
from app.repositories.user_repository import InMemoryUserRepository

def _auth_headers(subject: str = "authentik:user1") -> dict[str, str]:
    return {"X-Authentik-Subject": subject}


def test_models_list_and_usage_summary(client):
    reset_inmemory_model_repositories()
    repo = InMemoryUserRepository()
    repo.save(
        User(
            user_id="u_user1",
            subject_id="authentik:user1",
            tenant_id="t_default",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
    )
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    resp = client.get("/api/v1/models", headers=_auth_headers())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "models" in data
    assert data["models"]
    first_model = data["models"][0]
    assert "modelId" in first_model
    assert "defaultRoute" in first_model
    assert "internalEndpoint" not in first_model

    resp_usage = client.get("/api/v1/usage/summary", headers=_auth_headers())
    assert resp_usage.status_code == status.HTTP_200_OK
    usage = resp_usage.json()
    assert usage["userId"]
    assert usage["totalTokens"] >= 0
    assert usage["usedTokens"] >= 0


def test_removed_user_configuration_interfaces_are_not_exposed(client):
    reset_inmemory_model_repositories()
    headers = _auth_headers()

    assert client.get("/api/v1/models/bindings", headers=headers).status_code == status.HTTP_404_NOT_FOUND
    assert client.put(
        "/api/v1/models/gpt-4-mini/binding",
        headers=headers,
        json={"credentialId": "cred_001"},
    ).status_code == status.HTTP_404_NOT_FOUND
    assert client.get("/api/v1/credentials", headers=headers).status_code == status.HTTP_404_NOT_FOUND
    assert client.post(
        "/api/v1/credentials",
        headers=headers,
        json={"provider": "openai", "name": "default", "secret": "sk-test"},
    ).status_code == status.HTTP_404_NOT_FOUND

