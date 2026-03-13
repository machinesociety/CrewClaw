from fastapi import status

from app.core.dependencies import get_sqlalchemy_user_repository
from app.domain.users import User, UserRole, UserStatus
from app.repositories.user_repository import InMemoryUserRepository


def test_auth_me_unauthenticated(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    data = resp.json()
    assert data["code"] == "UNAUTHENTICATED"


def test_auth_me_ok_with_subject_header(client):
    repo = InMemoryUserRepository()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {"X-Authentik-Subject": "authentik:12345"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["authenticated"] is True
        assert data["userId"]
        assert data["subjectId"] == "authentik:12345"
        assert data["tenantId"] == "t_default"
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_auth_access_allowed_for_active_user(client):
    repo = InMemoryUserRepository()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {"X-Authentik-Subject": "authentik:active"}
        resp = client.get("/api/v1/auth/access", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["allowed"] is True
        assert data["reason"] is None
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_auth_access_disabled_user_blocked(client):
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
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {"X-Authentik-Subject": "authentik:disabled"}
        resp = client.get("/api/v1/auth/access", headers=headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        data = resp.json()
        assert data["code"] == "USER_DISABLED"
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)

