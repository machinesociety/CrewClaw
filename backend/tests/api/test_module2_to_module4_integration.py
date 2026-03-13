from fastapi import status

from app.core.dependencies import (
    get_sqlalchemy_user_repository,
)
from app.domain.users import User, UserRole, UserStatus
from app.repositories.user_repository import InMemoryUserRepository


def _auth_headers(subject: str) -> dict[str, str]:
    return {"X-Authentik-Subject": subject}


def test_module2_to_module4_integration(client):
    """
    集成测试：模块 2 提供用户与 runtime 资源基础，模块 4 提供模型、凭据与用量视图。
    """
    repo = InMemoryUserRepository()
    client.app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: repo
    try:
        # 通过模块 2 的 /internal/users/sync 创建设备用户
        resp_sync = client.post(
            "/internal/users/sync",
            json={"subject_id": "authentik:integration-user"},
        )
        assert resp_sync.status_code == status.HTTP_200_OK
        user_id = resp_sync.json()["userId"]

        # 确保 runtime binding 存在
        resp_binding = client.post(f"/internal/users/{user_id}/runtime-binding/ensure")
        assert resp_binding.status_code == status.HTTP_200_OK

        # 在同一用户上下文下走模块 4 主流程
        headers = _auth_headers("authentik:integration-user")

        # 创建凭据
        resp_cred = client.post(
            "/api/v1/credentials",
            headers=headers,
            json={"name": "integration-cred", "secret": "sk-..."},
        )
        assert resp_cred.status_code == status.HTTP_201_CREATED
        cred_id = resp_cred.json()["credential_id"]

        # 绑定模型
        resp_bind = client.put(
            "/api/v1/models/gpt-4-mini/binding",
            headers=headers,
            json={"credential_id": cred_id},
        )
        assert resp_bind.status_code == status.HTTP_200_OK
        bindings = resp_bind.json()["bindings"]
        assert any(
            b["model_id"] == "gpt-4-mini"
            and b["credential_id"] == cred_id
            and b["source"] == "user_owned"
            for b in bindings
        )

        # 用量摘要 user_id 与模块 2 的 userId 一致
        resp_usage = client.get("/api/v1/usage/summary", headers=headers)
        assert resp_usage.status_code == status.HTTP_200_OK
        usage = resp_usage.json()
        assert usage["user_id"] == user_id
    finally:
        client.app.dependency_overrides.pop(get_sqlalchemy_user_repository, None)

