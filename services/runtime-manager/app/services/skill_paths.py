from __future__ import annotations

from pathlib import Path


def skills_root_dir() -> Path:
    return Path("/var/lib/clawloops/shared/skills")


def skills_public_dir() -> Path:
    return skills_root_dir() / "public"


def skills_user_dir(user_id: str) -> Path:
    return skills_root_dir() / "users" / user_id


def skills_export_dir(user_id: str) -> Path:
    return Path("/var/lib/clawloops") / user_id / "openclaw-skills"


def container_workspace_skills_mount() -> str:
    return "/home/node/.openclaw/workspace/skills"
