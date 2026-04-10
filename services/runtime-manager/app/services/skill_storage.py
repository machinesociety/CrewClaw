from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import RuntimeManagerError
from app.services.skill_paths import skills_public_dir, skills_user_dir


@dataclass(frozen=True)
class SkillFile:
    name: str
    size: int
    modifiedAt: float


def _require_safe_skill_id(value: str) -> str:
    value = value.strip().replace("\\", "/")
    if not value or value.startswith("/") or ".." in value.split("/"):
        raise RuntimeManagerError("SKILL_INVALID_NAME", "invalid skill name", 400)
    base = value.split("/")[-1]
    if "." in base:
        base = base.rsplit(".", 1)[0]
    base = base.strip()
    if not base:
        raise RuntimeManagerError("SKILL_INVALID_NAME", "invalid skill name", 400)
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    normalized = "".join([c if c in allowed else "_" for c in base])
    normalized = normalized.strip("_")
    if not normalized:
        raise RuntimeManagerError("SKILL_INVALID_NAME", "invalid skill name", 400)
    return normalized


def _resolve_target_dir(scope: str, user_id: str | None) -> Path:
    if scope == "public":
        return skills_public_dir()
    if scope == "user":
        if not user_id:
            raise RuntimeManagerError("SKILL_MISSING_USER", "userId is required for user scope", 400)
        return skills_user_dir(user_id)
    raise RuntimeManagerError("SKILL_INVALID_SCOPE", "invalid scope", 400)


def list_skill_files(scope: str, user_id: str | None) -> list[SkillFile]:
    root = _resolve_target_dir(scope, user_id)
    if not root.exists():
        return []
    result: list[SkillFile] = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        skill_md = p / "SKILL.md"
        if not skill_md.exists() or not skill_md.is_file():
            continue
        st = skill_md.stat()
        result.append(SkillFile(name=p.name, size=st.st_size, modifiedAt=st.st_mtime))
    return result


def read_skill_file(scope: str, user_id: str | None, name: str) -> tuple[str, bytes]:
    skill_id = _require_safe_skill_id(name)
    root = _resolve_target_dir(scope, user_id)
    skill_dir = (root / skill_id).resolve()
    root_real = root.resolve()
    if root_real not in skill_dir.parents and skill_dir != root_real:
        raise RuntimeManagerError("SKILL_INVALID_NAME", "invalid skill name", 400)
    path = skill_dir / "SKILL.md"
    if not path.exists() or not path.is_file():
        raise RuntimeManagerError("SKILL_NOT_FOUND", "skill file not found", 404)
    return f"{skill_id}.md", path.read_bytes()


def write_skill_file(scope: str, user_id: str | None, name: str, data: bytes) -> SkillFile:
    skill_id = _require_safe_skill_id(name)
    root = _resolve_target_dir(scope, user_id)
    root.mkdir(parents=True, exist_ok=True)
    root_real = root.resolve()
    skill_dir = (root / skill_id).resolve()
    if root_real not in skill_dir.parents and skill_dir != root_real:
        raise RuntimeManagerError("SKILL_INVALID_NAME", "invalid skill name", 400)
    skill_dir.mkdir(parents=True, exist_ok=True)
    target = skill_dir / "SKILL.md"

    fd, temp_path = tempfile.mkstemp(prefix="skill.", suffix=".tmp", dir=str(skill_dir))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, target)
        try:
            os.chown(target, 1000, 1000)
        except PermissionError:
            pass
        target.chmod(0o664)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    st = target.stat()
    return SkillFile(name=skill_id, size=st.st_size, modifiedAt=st.st_mtime)


def write_skill_file_with_overwrite(scope: str, user_id: str | None, name: str, data: bytes, overwrite: bool) -> SkillFile:
    skill_id = _require_safe_skill_id(name)
    root = _resolve_target_dir(scope, user_id)
    root.mkdir(parents=True, exist_ok=True)
    root_real = root.resolve()
    skill_dir = (root / skill_id).resolve()
    if root_real not in skill_dir.parents and skill_dir != root_real:
        raise RuntimeManagerError("SKILL_INVALID_NAME", "invalid skill name", 400)
    if skill_dir.exists() and not overwrite:
        raise RuntimeManagerError("SKILL_ALREADY_EXISTS", "skill already exists", 409)
    return write_skill_file(scope=scope, user_id=user_id, name=skill_id, data=data)


def delete_skill(scope: str, user_id: str | None, name: str) -> None:
    skill_id = _require_safe_skill_id(name)
    root = _resolve_target_dir(scope, user_id)
    root_real = root.resolve()
    skill_dir = (root / skill_id).resolve()
    if root_real not in skill_dir.parents and skill_dir != root_real:
        raise RuntimeManagerError("SKILL_INVALID_NAME", "invalid skill name", 400)
    if not skill_dir.exists() or not skill_dir.is_dir():
        raise RuntimeManagerError("SKILL_NOT_FOUND", "skill not found", 404)
    for p in sorted(skill_dir.rglob("*"), reverse=True):
        if p.is_file() or p.is_symlink():
            p.unlink()
        elif p.is_dir():
            p.rmdir()
    skill_dir.rmdir()
