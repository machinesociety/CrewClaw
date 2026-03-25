import base64
import json

from app.core.authentik_groups import (
    effective_role_from_groups,
    parse_admin_group_slugs,
    parse_authentik_groups,
    parse_group_names_from_authentik_jwt,
)
from app.domain.users import UserRole


def test_parse_authentik_groups():
    assert parse_authentik_groups("a, b , c") == ["a", "b", "c"]
    assert parse_authentik_groups("") == []
    assert parse_authentik_groups("clawloops-admins") == ["clawloops-admins"]


def test_parse_admin_group_slugs():
    assert parse_admin_group_slugs("clawloops-admins, other") == {"clawloops-admins", "other"}


def test_effective_role_from_groups():
    admin = {"clawloops-admins"}
    assert effective_role_from_groups(["clawloops-admins"], admin) == UserRole.ADMIN
    assert effective_role_from_groups(["x", "clawloops-admins"], admin) == UserRole.ADMIN
    assert effective_role_from_groups([], admin) == UserRole.USER
    assert effective_role_from_groups(["other"], admin) == UserRole.USER


def _jwt_with_payload(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"e.{body}.x"


def test_parse_group_names_from_authentik_jwt():
    tok = _jwt_with_payload({"groups": ["clawloops-admins", "other"]})
    assert parse_group_names_from_authentik_jwt(tok) == ["clawloops-admins", "other"]
    assert parse_group_names_from_authentik_jwt(_jwt_with_payload({"groups": []})) == []
    assert parse_group_names_from_authentik_jwt(_jwt_with_payload({"sub": "x"})) is None
    assert parse_group_names_from_authentik_jwt("not-a-jwt") is None
