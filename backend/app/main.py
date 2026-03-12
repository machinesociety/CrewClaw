from fastapi import FastAPI

from app.api.v1 import auth as auth_api
from app.api.v1 import users as users_api
from app.api.v1 import runtime as runtime_api
from app.api.v1 import models as models_api
from app.api.v1 import credentials as credentials_api
from app.api.v1 import usage as usage_api
from app.api.v1 import workspace as workspace_api
from app.api.v1 import admin as admin_api
from app.api.v1 import internal as internal_api


def create_app() -> FastAPI:
    """
    创建 CrewClaw 控制面 FastAPI 应用实例。

    TODO:
    - 接入统一日志、请求 ID、中间件等。
    - 根据部署环境配置 OpenAPI 文档与调试开关。
    """
    app = FastAPI(
        title="CrewClaw Control Plane",
        version="0.1.0",
        description="CrewClaw 平台 MVP 控制面 API 服务。",
    )

    # 健康检查与根路径
    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {"service": "crewclaw-control-plane", "status": "ok"}

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict:
        # TODO: 后续可增加对数据库、下游服务的探活检查。
        return {"status": "healthy"}

    # 挂载 v1 路由
    app.include_router(auth_api.router, prefix="/api/v1")
    app.include_router(users_api.router, prefix="/api/v1")
    app.include_router(runtime_api.router, prefix="/api/v1")
    app.include_router(models_api.router, prefix="/api/v1")
    app.include_router(credentials_api.router, prefix="/api/v1")
    app.include_router(usage_api.router, prefix="/api/v1")
    app.include_router(workspace_api.router, prefix="/api/v1")
    app.include_router(admin_api.router, prefix="/api/v1")
    app.include_router(internal_api.router)

    return app


app = create_app()

