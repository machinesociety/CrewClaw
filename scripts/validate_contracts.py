#!/usr/bin/env python3
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "contracts" / "baseline-v0.2"


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON: {path} ({e})")


def assert_true(cond: bool, msg: str):
    if not cond:
        raise SystemExit(msg)


def main() -> int:
    enums = read_json(BASELINE_DIR / "enums.json")
    errors = read_json(BASELINE_DIR / "errors.json")
    boundary = read_json(BASELINE_DIR / "api-boundary.json")
    schema = read_json(BASELINE_DIR / "user_runtime_binding.schema.json")

    # Basic shape checks
    for obj, name in [(enums, "enums.json"), (errors, "errors.json"), (boundary, "api-boundary.json")]:
        assert_true(obj.get("baselineVersion") == "v0.2", f"{name}: baselineVersion must be v0.2")
        assert_true("frozenAt" in obj, f"{name}: missing frozenAt")

    assert_true(isinstance(enums.get("enums"), dict), "enums.json: enums must be an object")
    assert_true(isinstance(errors.get("errors"), list), "errors.json: errors must be an array")
    assert_true(isinstance(boundary.get("rules"), list), "api-boundary.json: rules must be an array")

    # Enums consistency checks (schema vs enums.json)
    enum_map = enums["enums"]
    desired = schema["properties"]["desiredState"].get("enum")
    observed = schema["properties"]["observedState"].get("enum")
    retention = schema["properties"]["retentionPolicy"].get("enum")

    assert_true(desired == enum_map.get("runtime.desiredState"), "schema: desiredState enum mismatch with enums.json")
    assert_true(observed == enum_map.get("runtime.observedState"), "schema: observedState enum mismatch with enums.json")
    assert_true(retention == enum_map.get("retentionPolicy"), "schema: retentionPolicy enum mismatch with enums.json")

    # User-facing forbid internalEndpoint rule must exist
    forbid_rule = next((r for r in boundary["rules"] if r.get("id") == "user_response_forbid_internalEndpoint"), None)
    assert_true(forbid_rule is not None, "api-boundary.json: missing rule user_response_forbid_internalEndpoint")
    assert_true("internalEndpoint" in (forbid_rule.get("forbidFields") or []), "api-boundary.json: forbidFields must include internalEndpoint")

    # Error registry uniqueness and required codes
    seen = set()
    for e in errors["errors"]:
        key = (e.get("http"), e.get("code"))
        assert_true(key not in seen, f"errors.json: duplicate error entry: {key}")
        seen.add(key)

    required = {(401, "UNAUTHENTICATED"), (403, "ACCESS_DENIED"), (403, "USER_DISABLED")}
    missing = sorted(required - seen)
    assert_true(not missing, f"errors.json: missing required errors: {missing}")

    print("OK: baseline-v0.2 contracts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

