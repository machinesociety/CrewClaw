from __future__ import annotations

import shutil
from pathlib import Path

from app.services.skill_paths import public_files_dir, runtime_public_copy_dir


def sync_public_copy_for_user(user_id: str) -> None:
    source = public_files_dir()
    source.mkdir(parents=True, exist_ok=True)
    target = runtime_public_copy_dir(user_id)
    legacy_target = Path("/var/lib/clawloops") / user_id / "workspace" / "public-area"

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    if legacy_target.exists() and legacy_target != target:
        shutil.rmtree(legacy_target)

    for item in source.iterdir():
        dst = target / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
