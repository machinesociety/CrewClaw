from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import RuntimeManagerError
from app.services.skill_paths import public_files_dir


@dataclass(frozen=True)
class PublicEntry:
    name: str
    isDir: bool
    size: int
    modifiedAt: float


def _safe_rel_path(value: str) -> Path:
    raw = (value or "").strip().replace("\\", "/")
    raw = raw.lstrip("/")
    if raw == "":
        return Path(".")
    parts = [p for p in raw.split("/") if p]
    if any(p in {".", ".."} for p in parts):
        raise RuntimeManagerError("PUBLIC_INVALID_PATH", "invalid path", 400)
    return Path(*parts)


def _resolve_under_root(root: Path, rel: Path) -> Path:
    root_real = root.resolve()
    target = (root / rel).resolve()
    if target == root_real:
        return target
    if root_real not in target.parents:
        raise RuntimeManagerError("PUBLIC_INVALID_PATH", "invalid path", 400)
    return target


def _sorted_dir_entries(target: Path) -> list[PublicEntry]:
    entries: list[PublicEntry] = []
    for p in target.iterdir():
        st = p.stat()
        entries.append(
            PublicEntry(
                name=p.name,
                isDir=p.is_dir(),
                size=0 if p.is_dir() else st.st_size,
                modifiedAt=st.st_mtime,
            )
        )
    entries.sort(key=lambda e: (not e.isDir, e.name.lower()))
    return entries


def list_public_entries(path: str, page: int, page_size: int) -> tuple[list[PublicEntry], int]:
    root = public_files_dir()
    root.mkdir(parents=True, exist_ok=True)
    if page < 1:
        raise RuntimeManagerError("PUBLIC_INVALID_PAGE", "invalid page", 400)
    if page_size < 1 or page_size > 100:
        raise RuntimeManagerError("PUBLIC_INVALID_PAGE_SIZE", "invalid page size", 400)
    rel = _safe_rel_path(path)
    target = _resolve_under_root(root, rel)
    if not target.exists():
        if rel == Path("."):
            return [], 0
        raise RuntimeManagerError("PUBLIC_NOT_FOUND", "path not found", 404)
    if not target.is_dir():
        raise RuntimeManagerError("PUBLIC_NOT_DIR", "path is not a directory", 400)
    all_entries = _sorted_dir_entries(target)
    total = len(all_entries)
    start = (page - 1) * page_size
    end = start + page_size
    return all_entries[start:end], total


def create_public_dir(path: str) -> None:
    root = public_files_dir()
    root.mkdir(parents=True, exist_ok=True)
    rel = _safe_rel_path(path)
    target = _resolve_under_root(root, rel)
    if target.exists() and target.is_file():
        raise RuntimeManagerError("PUBLIC_ALREADY_EXISTS", "file already exists", 409)
    target.mkdir(parents=True, exist_ok=True)


def read_public_file(path: str) -> tuple[str, bytes]:
    root = public_files_dir()
    root.mkdir(parents=True, exist_ok=True)
    rel = _safe_rel_path(path)
    target = _resolve_under_root(root, rel)
    if not target.exists() or not target.is_file():
        raise RuntimeManagerError("PUBLIC_NOT_FOUND", "file not found", 404)
    return target.name, target.read_bytes()


def write_public_file(path: str, data: bytes, overwrite: bool) -> PublicEntry:
    root = public_files_dir()
    root.mkdir(parents=True, exist_ok=True)
    rel = _safe_rel_path(path)
    target = _resolve_under_root(root, rel)
    if target.exists() and target.is_dir():
        raise RuntimeManagerError("PUBLIC_IS_DIR", "path is a directory", 400)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not overwrite:
        raise RuntimeManagerError("PUBLIC_ALREADY_EXISTS", "file already exists", 409)

    fd, temp_path = tempfile.mkstemp(prefix="public.", suffix=".tmp", dir=str(target.parent))
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
    return PublicEntry(name=target.name, isDir=False, size=st.st_size, modifiedAt=st.st_mtime)


def delete_public_path(path: str) -> None:
    root = public_files_dir()
    root.mkdir(parents=True, exist_ok=True)
    rel = _safe_rel_path(path)
    target = _resolve_under_root(root, rel)
    if not target.exists():
        raise RuntimeManagerError("PUBLIC_NOT_FOUND", "path not found", 404)
    if target.is_dir():
        if any(target.iterdir()):
            raise RuntimeManagerError("PUBLIC_DIR_NOT_EMPTY", "directory not empty", 409)
        target.rmdir()
    else:
        target.unlink()
