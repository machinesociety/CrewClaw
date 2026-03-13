import json
from pathlib import Path

from app.schemas.runtime import RuntimeBindingSnapshot, RuntimeStatusResponse
from app.schemas.workspace import WorkspaceEntryResponse


def test_user_runtime_binding_fields_match_contract():
    contracts_path = (
        Path(__file__).resolve().parents[2]
        / "contracts"
        / "baseline-v0.3"
        / "user_runtime_binding.schema.json"
    )
    schema = json.loads(contracts_path.read_text(encoding="utf-8"))

    contract_fields = set(schema["properties"].keys())
    model_fields = set(RuntimeBindingSnapshot.model_fields.keys())

    assert model_fields == contract_fields


def test_runtime_status_projection_fields_match_api_boundary():
    contracts_path = (
        Path(__file__).resolve().parents[2]
        / "contracts"
        / "baseline-v0.3"
        / "api-boundary.json"
    )
    boundary = json.loads(contracts_path.read_text(encoding="utf-8"))
    status_rule = next(rule for rule in boundary["rules"] if rule["id"] == "user_runtime_vs_status_boundary")

    assert set(RuntimeStatusResponse.model_fields.keys()) == set(status_rule["allowFields"])


def test_workspace_entry_does_not_expose_internal_endpoint():
    assert "internalEndpoint" not in WorkspaceEntryResponse.model_fields

