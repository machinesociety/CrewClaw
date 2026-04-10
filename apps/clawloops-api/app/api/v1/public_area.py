from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.auth import AuthContext
from app.core.dependencies import get_runtime_manager_client, require_active_user
from app.core.errors import AccessDeniedError
from app.infra.runtime_manager_client import RuntimeManagerClient


router = APIRouter(prefix="/public-area", tags=["public-area"])


class PublicFileWriteRequest(BaseModel):
    path: str
    content: str


@router.get("/files/list")
def list_public_files(
    path: str = "",
    page: int = 1,
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    return rm.list_public_entries(path=path, page=page, page_size=10)


@router.post("/files/upload")
async def upload_public_file(
    path: str = Form(...),
    overwrite: bool = Form(False),
    file: UploadFile = File(...),
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    content = await file.read()
    allow_overwrite = bool(overwrite) and bool(ctx.isAdmin)
    result = rm.upload_public_file(path=path, content=content, filename=file.filename or "file", overwrite=allow_overwrite)
    return result


@router.post("/files/mkdir")
def mkdir_public_dir(
    path: str = Form(...),
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    rm.mkdir_public_dir(path=path)
    return {"success": True}


@router.get("/files/read")
def read_public_file(
    path: str,
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    data, _headers = rm.download_public_file(path=path)
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="file is not utf-8 text")
    return {"content": content}


@router.put("/files/write")
def write_public_file(
    body: PublicFileWriteRequest,
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    if not ctx.isAdmin:
        raise AccessDeniedError()
    filename = body.path.split("/")[-1] or "file"
    rm.upload_public_file(
        path=body.path,
        content=body.content.encode("utf-8"),
        filename=filename,
        overwrite=True,
    )
    return {"success": True}


@router.get("/files/download")
def download_public_file(
    path: str,
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> Response:
    data, headers = rm.download_public_file(path=path)
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
    ctx: AuthContext = Depends(require_active_user),
    rm: RuntimeManagerClient = Depends(get_runtime_manager_client),
) -> dict:
    if not ctx.isAdmin:
        raise AccessDeniedError()
    rm.delete_public_path(path=path)
    return {"success": True}
