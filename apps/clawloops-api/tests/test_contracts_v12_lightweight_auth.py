import json
from pathlib import Path


def _contracts_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "contracts"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("contracts directory not found from test file path")


def _read_contract_file(filename: str) -> dict:
    path = _contracts_root() / "baseline-v0.12-lightweight-auth" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def test_v12_contract_files_exist_and_version_is_consistent():
    enums = _read_contract_file("enums.json")
    errors = _read_contract_file("errors.json")
    boundary = _read_contract_file("api-boundary.json")
    schema_runtime = _read_contract_file("user_runtime_binding.schema.json")
    schema_session_user = _read_contract_file("session_user.schema.json")

    assert enums["baselineVersion"] == "v0.12-lightweight-auth"
    assert errors["baselineVersion"] == "v0.12-lightweight-auth"
    assert boundary["baselineVersion"] == "v0.12-lightweight-auth"
    assert schema_runtime["$id"].endswith(":baseline-v0.12-lightweight-auth:UserRuntimeBinding")
    assert schema_session_user["$id"].endswith(":baseline-v0.12-lightweight-auth:SessionUser")


def test_v12_invitation_status_enum_is_frozen():
    enums = _read_contract_file("enums.json")["enums"]
    assert enums["invitation.status"] == ["pending", "consumed", "revoked"]


def test_v12_error_registry_contains_required_codes():
    error_codes = {entry["code"] for entry in _read_contract_file("errors.json")["errors"]}
    required_codes = {
        "UNAUTHENTICATED",
        "INVALID_CREDENTIALS",
        "USER_DISABLED",
        "PASSWORD_CHANGE_REQUIRED",
        "SESSION_ERROR",
        "INVITATION_ALREADY_CONSUMED",
        "INVITATION_REVOKED",
        "INVITATION_EXPIRED",
        "INVITATION_USERNAME_MISMATCH",
        "INVITATION_PASSWORD_INVALID",
        "CURRENT_PASSWORD_INCORRECT",
        "PASSWORD_CHANGE_INVALID",
    }
    assert required_codes.issubset(error_codes)


def test_v12_boundary_contains_auth_access_and_post_login_forbid_rules():
    rules = _read_contract_file("api-boundary.json")["rules"]
    rule_ids = {rule["id"] for rule in rules}
    assert "auth_access_always_200" in rule_ids
    assert "forbid_auth_post_login" in rule_ids

