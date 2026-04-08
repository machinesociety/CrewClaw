from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from fastapi.responses import Response
from app.core.dependencies import require_active_user, get_runtime_service
from app.services.runtime_service import RuntimeService
import logging

router = APIRouter(tags=["files"])
logger = logging.getLogger(__name__)


class FileListResponse(BaseModel):
    files: list[dict]


class FileReadResponse(BaseModel):
    content: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


@router.get("/files/list")
async def list_files(
    path: str,
    user = Depends(require_active_user),
    runtime_service: RuntimeService = Depends(get_runtime_service),
) -> FileListResponse:
    """
    列出容器内的文件
    """
    try:
        binding = runtime_service.get_user_binding(user.userId)
        if not binding or not binding.runtimeId:
            raise HTTPException(status_code=400, detail="No container available")
        
        files = runtime_service.list_files(binding.runtimeId, path)
        return FileListResponse(files=files)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to list files")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/files/read")
async def read_file(
    path: str,
    user = Depends(require_active_user),
    runtime_service: RuntimeService = Depends(get_runtime_service),
) -> FileReadResponse:
    """
    读取容器内的文件内容
    """
    try:
        binding = runtime_service.get_user_binding(user.userId)
        if not binding or not binding.runtimeId:
            raise HTTPException(status_code=400, detail="No container available")
        
        content = runtime_service.read_file(binding.runtimeId, path)
        return FileReadResponse(content=content)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to read file")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.put("/files/write")
async def write_file(
    request: FileWriteRequest,
    user = Depends(require_active_user),
    runtime_service: RuntimeService = Depends(get_runtime_service),
) -> dict:
    """
    写入文件内容到容器内
    """
    try:
        binding = runtime_service.get_user_binding(user.userId)
        if not binding or not binding.runtimeId:
            raise HTTPException(status_code=400, detail="No container available")
        
        runtime_service.write_file(binding.runtimeId, request.path, request.content)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to write file")
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


@router.post("/files/upload")
async def upload_file(
    path: str = Form(...),
    file: UploadFile = File(...),
    user = Depends(require_active_user),
    runtime_service: RuntimeService = Depends(get_runtime_service),
) -> dict:
    """
    上传文件到容器内
    """
    try:
        binding = runtime_service.get_user_binding(user.userId)
        if not binding or not binding.runtimeId:
            raise HTTPException(status_code=400, detail="No container available")
        
        content = await file.read()
        runtime_service.write_file(binding.runtimeId, path, content)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to upload file")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/files/download")
async def download_file(
    path: str,
    user = Depends(require_active_user),
    runtime_service: RuntimeService = Depends(get_runtime_service),
) -> Response:
    """
    从容器内下载文件
    """
    try:
        binding = runtime_service.get_user_binding(user.userId)
        if not binding or not binding.runtimeId:
            raise HTTPException(status_code=400, detail="No container available")
        
        content = runtime_service.read_file(binding.runtimeId, path)
        filename = path.split("/")[-1]
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to download file")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")
