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
from app.services.runtime_executor import RuntimeExecutor
from app.services.skill_exporter import sync_all_skill_exports, sync_skill_export
from app.services.skill_storage import list_skill_files, read_skill_file, write_skill_file


class FileListResponse(BaseModel):
    files: list[dict]


class FileReadResponse(BaseModel):
    content: str


class FileWriteRequest(BaseModel):
    runtimeId: str
    path: str
    content: str
    isBinary: bool = False


class SkillListItem(BaseModel):
    name: str
    size: int
    modifiedAt: float


class SkillListResponse(BaseModel):
    files: list[SkillListItem]

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
    "/skills/list",
    response_model=SkillListResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def list_skills(scope: str, userId: str | None = None) -> SkillListResponse:
    try:
        files = list_skill_files(scope=scope, user_id=userId)
        return SkillListResponse(files=[SkillListItem(name=f.name, size=f.size, modifiedAt=f.modifiedAt) for f in files])
    except RuntimeManagerError as err:
        _raise_http(err)


@router.post(
    "/skills/upload",
    response_model=SkillListItem,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_skill(
    scope: str = Form(...),
    userId: str | None = Form(None),
    name: str | None = Form(None),
    file: UploadFile = File(...),
) -> SkillListItem:
    try:
        content = await file.read()
        target_name = name or file.filename or "skill"
        saved = write_skill_file(scope=scope, user_id=userId, name=target_name, data=content)
        if scope == "user" and userId is not None:
            sync_skill_export(userId)
        if scope == "public":
            sync_all_skill_exports()
        return SkillListItem(name=saved.name, size=saved.size, modifiedAt=saved.modifiedAt)
    except RuntimeManagerError as err:
        _raise_http(err)


@router.get(
    "/skills/download",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def download_skill(scope: str, name: str, userId: str | None = None) -> Response:
    try:
        filename, data = read_skill_file(scope=scope, user_id=userId, name=name)
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except RuntimeManagerError as err:
        _raise_http(err)
