from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.core.auth import AuthContext
from app.core.dependencies import get_runtime_manager_client, require_active_user
from app.core.errors import AccessDeniedError
from app.infra.runtime_manager_client import RuntimeManagerClient


router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/me/list")
def list_my_skills(
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    return {"files": rm.list_skills(scope="user", user_id=ctx.userId)}


@router.post("/me/upload")
async def upload_my_skill(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    content = await file.read()
    result = rm.upload_skill(
        scope="user",
        user_id=ctx.userId,
        content=content,
        filename=file.filename or "skill",
        name=name,
    )
    return result


@router.get("/me/download")
def download_my_skill(
    name: str,
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> Response:
    data, _headers = rm.download_skill(scope="user", user_id=ctx.userId, name=name)
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.get("/public/list")
def list_public_skills(
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    return {"files": rm.list_skills(scope="public")}


@router.get("/public/download")
def download_public_skill(
    name: str,
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> Response:
    data, _headers = rm.download_skill(scope="public", name=name)
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.post("/public/upload")
async def upload_public_skill(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    if not ctx.isAdmin:
        raise AccessDeniedError()
    content = await file.read()
    result = rm.upload_skill(
        scope="public",
        user_id=None,
        content=content,
        filename=file.filename or "skill",
        name=name,
    )
    return result
