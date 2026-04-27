from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import RuntimeManagerError
from app.core.settings import get_settings
from app.services.skill_paths import public_files_dir, public_root_dir, runtime_public_copy_dir


@dataclass(frozen=True)
class PublicEntry:
    name: str
    isDir: bool
    size: int
    modifiedAt: float


def public_root_dir() -> Path:
    settings = get_settings()
    return Path(settings.runtime_public_files_mount_dir)


def legacy_public_root_dir() -> Path:
    settings = get_settings()
    return Path(settings.runtime_user_files_mount_dir) / "shared" / "public"


def runtime_public_copy_dir(user_id: str) -> Path:
    settings = get_settings()
    return Path(settings.runtime_user_files_mount_dir) / user_id / "workspace" / "public"


def _migrate_legacy_public_root() -> None:
    target_root = public_root_dir()
    legacy_root = legacy_public_root_dir()

    if not legacy_root.exists():
        return

    target_root.mkdir(parents=True, exist_ok=True)

    for item in legacy_root.iterdir():
        destination = target_root / item.name
        if destination.exists():
            continue
        shutil.move(str(item), str(destination))

    try:
        if not any(legacy_root.iterdir()):
            legacy_root.rmdir()
            shared_root = legacy_root.parent
            if shared_root.exists() and not any(shared_root.iterdir()):
                shared_root.rmdir()
    except OSError:
        pass


def _safe_rel_path(value: str) -> Path:
    raw = (value or "").strip().replace("\\", "/").lstrip("/")
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


def resolve_public_root(user_id: str | None = None) -> Path:
    if user_id:
        return runtime_public_copy_dir(user_id)
    _migrate_legacy_public_root()
    _migrate_legacy_public_files_dir()
    return public_root_dir()

def _migrate_legacy_public_files_dir() -> None:
    root = public_root_dir()
    legacy = root / "files"
    if not legacy.exists() or not legacy.is_dir():
        return
    root.mkdir(parents=True, exist_ok=True)
    for item in legacy.iterdir():
        target = root / item.name
        if target.exists():
            continue
        if item.is_dir():
            shutil.move(str(item), str(target))
        else:
            shutil.move(str(item), str(target))
    if legacy.exists():
        shutil.rmtree(legacy)
>>>>>>> origin/qsh774


def _sorted_dir_entries(target: Path) -> list[PublicEntry]:
    entries: list[PublicEntry] = []
    for path in target.iterdir():
        stat = path.stat()
        entries.append(
            PublicEntry(
                name=path.name,
                isDir=path.is_dir(),
                size=0 if path.is_dir() else stat.st_size,
                modifiedAt=stat.st_mtime,
            )
        )
    entries.sort(key=lambda entry: (not entry.isDir, entry.name.lower()))
    return entries


def list_public_entries(path: str, page: int, page_size: int, user_id: str | None = None) -> tuple[list[PublicEntry], int]:
    root = resolve_public_root(user_id)
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


def create_public_dir(path: str, user_id: str | None = None) -> None:
    root = resolve_public_root(user_id)
    root.mkdir(parents=True, exist_ok=True)
    rel = _safe_rel_path(path)
    target = _resolve_under_root(root, rel)
    if target.exists() and target.is_file():
        raise RuntimeManagerError("PUBLIC_ALREADY_EXISTS", "file already exists", 409)
    target.mkdir(parents=True, exist_ok=True)


def read_public_file(path: str, user_id: str | None = None) -> tuple[str, bytes]:
    root = resolve_public_root(user_id)
    root.mkdir(parents=True, exist_ok=True)
    rel = _safe_rel_path(path)
    target = _resolve_under_root(root, rel)
    if not target.exists() or not target.is_file():
        raise RuntimeManagerError("PUBLIC_NOT_FOUND", "file not found", 404)
    return target.name, target.read_bytes()


def write_public_file(path: str, data: bytes, overwrite: bool, user_id: str | None = None) -> PublicEntry:
    root = resolve_public_root(user_id)
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
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
        try:
            os.chown(target, 1000, 1000)
        except PermissionError:
            pass
        target.chmod(0o664)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    stat = target.stat()
    return PublicEntry(name=target.name, isDir=False, size=stat.st_size, modifiedAt=stat.st_mtime)


def delete_public_path(path: str, user_id: str | None = None) -> None:
    root = resolve_public_root(user_id)
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


def sync_public_copy_for_user(user_id: str) -> None:
    source = public_root_dir()
    source.mkdir(parents=True, exist_ok=True)
    target = runtime_public_copy_dir(user_id)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        dst = target / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
