from fastapi import status

from app.core.dependencies import get_sqlalchemy_user_repository
from app.domain.users import User, UserRole, UserStatus
from app.repositories.user_repository import InMemoryUserRepository


def _repo_with_disabled_user():
    repo = InMemoryUserRepository()
    repo.save(
        User(
            user_id="u_disabled",
            subject_id="authentik:disabled",
            tenant_id="t_default",
            role=UserRole.USER,
            status=UserStatus.DISABLED,
        )
    )
    return repo


def test_disabled_user_cannot_start_runtime(client):
    repo = _repo_with_disabled_user()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {"X-Authentik-Subject": "authentik:disabled"}
        resp = client.post("/api/v1/users/me/runtime/start", headers=headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        data = resp.json()
        assert data["code"] == "USER_DISABLED"
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_disabled_user_cannot_access_quota(client):
    repo = _repo_with_disabled_user()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {"X-Authentik-Subject": "authentik:disabled"}
        resp = client.get("/api/v1/users/me/quota", headers=headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        data = resp.json()
        assert data["code"] == "USER_DISABLED"
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_disabled_user_cannot_access_runtime_status(client):
    repo = _repo_with_disabled_user()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {"X-Authentik-Subject": "authentik:disabled"}
        resp = client.get("/api/v1/users/me/runtime/status", headers=headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        data = resp.json()
        assert data["code"] == "USER_DISABLED"
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)

