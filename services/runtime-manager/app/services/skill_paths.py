from __future__ import annotations

from pathlib import Path


def public_root_dir() -> Path:
    return Path("/var/lib/clawloops/shared/public")


def skills_root_dir() -> Path:
    new_root = public_root_dir() / "skills"
    if new_root.exists() or public_root_dir().exists():
        return new_root
    return Path("/var/lib/clawloops/shared/skills")


def public_files_dir() -> Path:
    return public_root_dir()


def runtime_public_copy_dir(user_id: str) -> Path:
    return Path("/var/lib/clawloops") / user_id / "workspace" / "public"


def skills_public_dir() -> Path:
    root = skills_root_dir()
    if root.name == "skills" and root.parent.name == "public":
        return root
    return root / "public"


def skills_user_dir(user_id: str) -> Path:
    return skills_root_dir() / "users" / user_id


def skills_export_dir(user_id: str) -> Path:
    return Path("/var/lib/clawloops") / user_id / "openclaw-skills"


def container_workspace_skills_mount() -> str:
    return "/home/node/.openclaw/workspace/skills"
