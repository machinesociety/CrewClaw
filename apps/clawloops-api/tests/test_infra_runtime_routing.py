from pathlib import Path


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "infra" / "compose" / "docker-compose.yml"
        if candidate.exists():
            return parent
    raise FileNotFoundError("repo root not found from test file path")


def test_runtime_manager_route_does_not_overlap_runtime_prefix():
    compose_path = _repo_root() / "infra" / "compose" / "docker-compose.yml"
    compose_text = compose_path.read_text(encoding="utf-8")

    assert "PathPrefix(`/runtime-manager`)" in compose_text
    assert "PathPrefix(`/runtime`)" not in compose_text
    assert "traefik.http.middlewares.runtime_manager_strip.stripprefix.prefixes=/runtime-manager" in compose_text
