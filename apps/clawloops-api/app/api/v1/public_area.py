from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.core.auth import AuthContext
from app.core.dependencies import get_runtime_manager_client, require_active_user
from app.core.errors import AccessDeniedError
from app.infra.runtime_manager_client import RuntimeManagerClient


router = APIRouter(prefix="/public-area", tags=["public-area"])


def _use_global_scope(ctx: AuthContext, scope: str) -> bool:
    return bool(ctx.isAdmin) and scope == "global"


@router.get("/files/list")
def list_public_files(
    path: str = "",
    page: int = 1,
    scope: Literal["user", "global"] = "user",
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    if _use_global_scope(ctx, scope):
        return rm.list_public_entries(path=path, page=page, page_size=10)
    return rm.list_public_entries(path=path, page=page, page_size=10, user_id=ctx.userId)


@router.post("/files/upload")
async def upload_public_file(
    path: str = Form(...),
    overwrite: bool = Form(False),
    scope: Literal["user", "global"] = Form("user"),
    file: UploadFile = File(...),
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    content = await file.read()
    use_global = _use_global_scope(ctx, scope)
    allow_overwrite = bool(overwrite) if not use_global else bool(overwrite) and bool(ctx.isAdmin)
    result = rm.upload_public_file(
        path=path,
        content=content,
        filename=file.filename or "file",
        overwrite=allow_overwrite,
        user_id=None if use_global else ctx.userId,
    )
    return result


@router.post("/files/mkdir")
def mkdir_public_dir(
    path: str = Form(...),
    scope: Literal["user", "global"] = Form("user"),
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    if _use_global_scope(ctx, scope):
        rm.mkdir_public_dir(path=path)
    else:
        rm.mkdir_public_dir(path=path, user_id=ctx.userId)
    return {"success": True}


@router.get("/files/download")
def download_public_file(
    path: str,
    scope: Literal["user", "global"] = "user",
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> Response:
    if _use_global_scope(ctx, scope):
        data, headers = rm.download_public_file(path=path)
    else:
        data, headers = rm.download_public_file(path=path, user_id=ctx.userId)
    filename = "download"
    dispo = headers.get("content-disposition") or headers.get("Content-Disposition")
    if dispo and "filename=" in dispo:
        filename = dispo.split("filename=", 1)[1].strip().strip('"')
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/files/delete")
def delete_public_file(
    path: str,
    scope: Literal["user", "global"] = "user",
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    if _use_global_scope(ctx, scope):
        if not ctx.isAdmin:
            raise AccessDeniedError()
        rm.delete_public_path(path=path)
    else:
        rm.delete_public_path(path=path, user_id=ctx.userId)
    return {"success": True}
