from __future__ import annotations

import shutil
from pathlib import Path

from app.services.skill_paths import skills_export_dir, skills_public_dir, skills_user_dir


def _copy_skill_dirs(src_root: Path, dst_root: Path) -> None:
    if not src_root.exists():
        return
    for p in sorted(src_root.iterdir()):
        if not p.is_dir():
            continue
        target = dst_root / p.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(p, target, dirs_exist_ok=True)


def sync_skill_export(user_id: str) -> Path:
    export_root = skills_export_dir(user_id)
    export_root.mkdir(parents=True, exist_ok=True)
    for item in export_root.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    _copy_skill_dirs(skills_public_dir(), export_root)
    _copy_skill_dirs(skills_user_dir(user_id), export_root)
    return export_root


def sync_all_skill_exports() -> None:
    root = Path("/var/lib/clawloops")
    if not root.exists():
        return
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        if (p / "openclaw-skills").exists():
            sync_skill_export(p.name)
