import os
from pathlib import Path
from typing import List, Dict


class FileStorageManager:
    """
    管理服务器本地文件存储
    """
    def __init__(self, base_path: str = "/app/user-files"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
    
    def create_user_directory(self, username: str) -> str:
        """
        为用户创建目录
        """
        user_path = os.path.join(self.base_path, username)
        os.makedirs(user_path, exist_ok=True)
        # 创建工作区目录
        workspace_path = os.path.join(user_path, "workspace")
        os.makedirs(workspace_path, exist_ok=True)
        # 创建配置目录
        config_path = os.path.join(user_path, "openclaw-config")
        os.makedirs(config_path, exist_ok=True)
        return user_path
    
    def list_files(self, username: str, path: str = "") -> List[Dict]:
        """
        列出用户文件
        """
        user_path = os.path.join(self.base_path, username)
        if not os.path.exists(user_path):
            return []
        
        # 构建完整路径
        target_path = os.path.join(user_path, "workspace", path)
        if not os.path.exists(target_path):
            return []
        
        files = []
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            is_directory = os.path.isdir(item_path)
            size = os.path.getsize(item_path) if not is_directory else 0
            modified_at = os.path.getmtime(item_path)
            
            files.append({
                "id": f"{username}/{path}/{item}",
                "username": username,
                "path": os.path.join(path, item),
                "name": item,
                "size": size,
                "modifiedAt": modified_at,
                "isDirectory": is_directory
            })
        
        return files
    
    def delete_file(self, username: str, path: str) -> bool:
        """
        删除用户文件
        """
        user_path = os.path.join(self.base_path, username)
        if not os.path.exists(user_path):
            return False
        
        try:
            # 如果path为空，删除整个用户目录
            if not path:
                import shutil
                shutil.rmtree(user_path)
                return True
            
            # 否则，删除特定的路径
            target_path = os.path.join(user_path, "workspace", path)
            if not os.path.exists(target_path):
                return False
            
            if os.path.isdir(target_path):
                import shutil
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
            return True
        except Exception:
            return False
    
    def read_file(self, username: str, path: str) -> bytes:
        """
        读取用户文件内容
        """
        user_path = os.path.join(self.base_path, username)
        if not os.path.exists(user_path):
            raise FileNotFoundError("User directory not found")
        
        # 构建完整路径
        target_path = os.path.join(user_path, "workspace", path)
        if not os.path.exists(target_path) or os.path.isdir(target_path):
            raise FileNotFoundError("File not found")
        
        with open(target_path, "rb") as f:
            return f.read()
    
    def get_all_users(self) -> List[str]:
        """
        获取所有用户
        """
        users = []
        if os.path.exists(self.base_path):
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                workspace_path = os.path.join(item_path, "workspace")
                config_path = os.path.join(item_path, "openclaw-config")
                if os.path.isdir(item_path) and os.path.isdir(workspace_path) and os.path.isdir(config_path):
                    users.append(item)
        return users


class UserFileService:
    """
    提供用户文件管理的业务逻辑
    """
    def __init__(self, storage_manager: FileStorageManager):
        self.storage_manager = storage_manager
    
    def get_users(self) -> List[Dict]:
        """
        获取所有用户的文件统计信息
        """
        users = []
        for username in self.storage_manager.get_all_users():
            # 统计用户文件数量和总大小
            files = self.storage_manager.list_files(username)
            file_count = len(files)
            total_size = sum(file["size"] for file in files)
            
            users.append({
                "username": username,
                "fileCount": file_count,
                "totalSize": total_size
            })
        return users
    
    def get_user_files(self, username: str, path: str = "") -> List[Dict]:
        """
        获取特定用户的文件列表（只返回目录）
        """
        files = self.storage_manager.list_files(username, path)
        # 只返回目录，过滤掉文件
        return [file for file in files if file["isDirectory"]]
    
    def delete_file(self, username: str, path: str) -> bool:
        """
        删除特定用户的文件
        """
        return self.storage_manager.delete_file(username, path)
    
    def download_file(self, username: str, path: str) -> bytes:
        """
        下载特定用户的文件
        """
        return self.storage_manager.read_file(username, path)
