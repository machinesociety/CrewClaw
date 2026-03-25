import base64
import json

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
        assert data["user"]["userId"]
        assert data["user"]["subjectId"] == "authentik:12345"
        assert data["user"]["tenantId"] == "t_default"
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
        # v0.11: auth/access 永远 200，仅用于状态判断
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["allowed"] is False
        assert data["reason"] == "USER_DISABLED"
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_auth_options_available(client):
    resp = client.get("/api/v1/auth/options")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["provider"] == "authentik"
    assert isinstance(data["methods"], list)
    assert any(method["type"] == "local_password" and method["enabled"] is True for method in data["methods"])


def _jwt_with_groups(groups: list) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"groups": groups}).encode()).decode().rstrip("=")
    return f"e.{body}.x"


def test_auth_me_promotes_to_admin_when_jwt_claims_groups_only(client):
    repo = InMemoryUserRepository()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {
            "X-Authentik-Subject": "authentik:jwt-admin",
            "X-Authentik-Jwt": _jwt_with_groups(["clawloops-admins"]),
        }
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["user"]["role"] == "admin"
        assert data["user"]["isAdmin"] is True
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_auth_me_promotes_when_authentik_builtin_admins_group_name(client):
    """Authentik 默认内置组名为 authentik Admins（与 clawloops-admins 不同）。"""
    repo = InMemoryUserRepository()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {
            "X-Authentik-Subject": "authentik:builtin-admin",
            "X-Authentik-Groups": "authentik Admins",
        }
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["user"]["role"] == "admin"
        assert data["user"]["isAdmin"] is True
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_auth_me_promotes_to_admin_when_authentik_groups_match(client):
    repo = InMemoryUserRepository()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {
            "X-Authentik-Subject": "authentik:group-admin",
            "X-Authentik-Groups": "clawloops-admins",
        }
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["user"]["role"] == "admin"
        assert data["user"]["isAdmin"] is True
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_auth_me_demotes_admin_when_groups_header_present_but_not_admin_group(client):
    repo = InMemoryUserRepository()
    repo.save(
        User(
            user_id="u_admin",
            subject_id="authentik:demote-me",
            tenant_id="t_default",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
    )
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {
            "X-Authentik-Subject": "authentik:demote-me",
            "X-Authentik-Groups": "other-group",
        }
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["user"]["role"] == "user"
        assert data["user"]["isAdmin"] is False
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)


def test_auth_me_preserves_admin_when_groups_header_absent(client):
    repo = InMemoryUserRepository()
    repo.save(
        User(
            user_id="u_admin2",
            subject_id="authentik:keep-admin",
            tenant_id="t_default",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
    )
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        headers = {"X-Authentik-Subject": "authentik:keep-admin"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["user"]["role"] == "admin"
        assert data["user"]["isAdmin"] is True
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)

