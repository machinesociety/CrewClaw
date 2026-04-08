from __future__ import annotations

from fastapi import APIRouter, HTTPException
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


class FileListResponse(BaseModel):
    files: list[dict]


class FileReadResponse(BaseModel):
    content: str


class FileWriteRequest(BaseModel):
    runtimeId: str
    path: str
    content: str
    isBinary: bool = False

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
