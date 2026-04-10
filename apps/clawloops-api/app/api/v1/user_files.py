from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import require_admin_user
from app.core.auth import AuthContext
from app.services.user_file_service import UserFileService
from app.core.dependencies import get_user_file_service

router = APIRouter(tags=["user-files"])


@router.get("/admin/user-files/users")
async def get_users(
    ctx: AuthContext = Depends(require_admin_user),
    user_file_service: UserFileService = Depends(get_user_file_service),
):
    """
    获取所有用户的文件夹列表
    """
    try:
        users = user_file_service.get_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")


@router.get("/admin/user-files/{username}/list")
async def get_user_files(
    username: str,
    path: str = "",
    ctx: AuthContext = Depends(require_admin_user),
    user_file_service: UserFileService = Depends(get_user_file_service),
):
    """
    获取特定用户的文件列表（只能查看一级目录）
    """
    try:
        # 确保只能查看一级目录
        if path and "/" in path:
            raise HTTPException(status_code=403, detail="只能查看一级目录")
        
        files = user_file_service.get_user_files(username, path)
        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user files: {str(e)}")


@router.delete("/admin/user-files/{username}/delete")
async def delete_file(
    username: str,
    path: str,
    ctx: AuthContext = Depends(require_admin_user),
    user_file_service: UserFileService = Depends(get_user_file_service),
):
    """
    删除特定用户的文件
    """
    try:
        # 确保只能删除一级目录中的文件
        if "/" in path:
            raise HTTPException(status_code=403, detail="只能删除一级目录中的文件")
        
        success = user_file_service.delete_file(username, path)
        if success:
            return {"success": True, "message": "文件删除成功"}
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
