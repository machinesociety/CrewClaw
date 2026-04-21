from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

from app.core.errors import RuntimeManagerError
from app.core.settings import get_settings
from app.schemas.contracts import (
    ContainerStateResponse,
    DeleteContainerRequest,
    EnsureContainerRequest,
    ErrorResponse,
    StopContainerRequest,
)
from app.services.public_storage import (
    create_public_dir,
    delete_public_path,
    list_public_entries,
    read_public_file,
    resolve_public_root,
    write_public_file,
)
from app.services.runtime_executor import RuntimeExecutor


class FileListResponse(BaseModel):
    files: list[dict]


class FileReadResponse(BaseModel):
    content: str


class FileWriteRequest(BaseModel):
    runtimeId: str
    path: str
    content: str
    isBinary: bool = False


class PublicListItem(BaseModel):
    name: str
    isDir: bool
    size: int
    modifiedAt: float


class PublicListResponse(BaseModel):
    entries: list[PublicListItem]
    rootPath: str
    page: int
    pageSize: int
    total: int
    totalPages: int

router = APIRouter(prefix="/internal/runtime-manager", tags=["runtime-manager"])


def _raise_http(err: RuntimeManagerError) -> None:
    raise HTTPException(status_code=err.status_code, detail={"code": err.code, "message": err.message})


@router.post(
    "/containers/ensure-running",
    response_model=ContainerStateResponse,
    responses={409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def ensure_running(body: EnsureContainerRequest) -> ContainerStateResponse:
    executor = RuntimeExecutor(get_settings())
    try:
        return executor.ensure_running(body)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.post(
    "/containers/stop",
    response_model=ContainerStateResponse,
    responses={409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def stop_container(body: StopContainerRequest) -> ContainerStateResponse:
    executor = RuntimeExecutor(get_settings())
    try:
        return executor.stop(body)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.post(
    "/containers/delete",
    response_model=ContainerStateResponse,
    responses={409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_container(body: DeleteContainerRequest) -> ContainerStateResponse:
    executor = RuntimeExecutor(get_settings())
    try:
        return executor.delete(body)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.get(
    "/containers/{runtime_id}",
    response_model=ContainerStateResponse,
    responses={409: {"model": ErrorResponse}},
)
def get_container(runtime_id: str) -> ContainerStateResponse:
    executor = RuntimeExecutor(get_settings())
    try:
        return executor.get_state(runtime_id)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.get(
    "/files/list",
    response_model=FileListResponse,
    responses={500: {"model": ErrorResponse}},
)
def list_files(runtimeId: str, path: str) -> FileListResponse:
    executor = RuntimeExecutor(get_settings())
    try:
        container = executor._get_single_container(runtimeId)
        if not container:
            raise RuntimeManagerError(
                "CONTAINER_NOT_FOUND",
                f"container not found for runtimeId: {runtimeId}",
                404,
            )
        files = executor.list_files(container.id, path)
        return FileListResponse(files=files)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.get(
    "/files/read",
    response_model=FileReadResponse,
    responses={500: {"model": ErrorResponse}},
)
def read_file(runtimeId: str, path: str) -> FileReadResponse:
    executor = RuntimeExecutor(get_settings())
    try:
        container = executor._get_single_container(runtimeId)
        if not container:
            raise RuntimeManagerError(
                "CONTAINER_NOT_FOUND",
                f"container not found for runtimeId: {runtimeId}",
                404,
            )
        content = executor.read_file(container.id, path)
        return FileReadResponse(content=content)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.put(
    "/files/write",
    responses={500: {"model": ErrorResponse}},
)
def write_file(body: FileWriteRequest) -> dict:
    executor = RuntimeExecutor(get_settings())
    try:
        container = executor._get_single_container(body.runtimeId)
        if not container:
            raise RuntimeManagerError(
                "CONTAINER_NOT_FOUND",
                f"container not found for runtimeId: {body.runtimeId}",
                404,
            )
        
        # 处理二进制内容
        content = body.content
        if body.isBinary:
            import base64
            content = base64.b64decode(content)
        
        executor.write_file(container.id, body.path, content)
        return {"success": True}
    except RuntimeManagerError as err:
        _raise_http(err)


@router.get(
    "/public/files/list",
    response_model=PublicListResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def list_public_files(path: str = "", page: int = 1, pageSize: int = 10, userId: str | None = None) -> PublicListResponse:
    try:
        entries, total = list_public_entries(path=path, page=page, page_size=pageSize, user_id=userId)
        total_pages = (total + pageSize - 1) // pageSize if total > 0 else 1
        if page > total_pages:
            page = total_pages
            entries, total = list_public_entries(path=path, page=page, page_size=pageSize, user_id=userId)
        return PublicListResponse(
            entries=[PublicListItem(name=e.name, isDir=e.isDir, size=e.size, modifiedAt=e.modifiedAt) for e in entries],
            rootPath=str(resolve_public_root(userId)),
            page=page,
            pageSize=pageSize,
            total=total,
            totalPages=total_pages,
        )
    except RuntimeManagerError as err:
        _raise_http(err)


@router.post(
    "/public/files/mkdir",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def mkdir_public_dir(path: str = Form(...), userId: str | None = Form(None)) -> dict:
    try:
        create_public_dir(path=path, user_id=userId)
        return {"success": True}
    except RuntimeManagerError as err:
        _raise_http(err)


@router.get(
    "/public/files/download",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def download_public_file(path: str, userId: str | None = None) -> Response:
    try:
        filename, data = read_public_file(path=path, user_id=userId)
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except RuntimeManagerError as err:
        _raise_http(err)


@router.post(
    "/public/files/upload",
    response_model=PublicListItem,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_public_file(
    path: str = Form(...),
    overwrite: bool = Form(False),
    userId: str | None = Form(None),
    file: UploadFile = File(...),
) -> PublicListItem:
    try:
        content = await file.read()
        saved = write_public_file(path=path, data=content, overwrite=overwrite, user_id=userId)
        return PublicListItem(name=saved.name, isDir=saved.isDir, size=saved.size, modifiedAt=saved.modifiedAt)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.delete(
    "/public/files/delete",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_public_file(path: str, userId: str | None = None) -> dict:
    try:
        delete_public_path(path=path, user_id=userId)
        return {"success": True}
    except RuntimeManagerError as err:
        _raise_http(err)
