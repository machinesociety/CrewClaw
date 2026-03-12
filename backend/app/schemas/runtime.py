from pydantic import BaseModel


class UserQuotaResponse(BaseModel):
    """
    TODO: 与实际 quota 模型对齐（tokens、天/月度等维度）。
    """

    user_id: str
    total_tokens: int
    used_tokens: int


class UserRuntimeBindingResponse(BaseModel):
    """
    对应 UserRuntimeBinding 冻结结构的用户侧视图。
    """

    user_id: str
    runtime_id: str
    volume_id: str
    image_ref: str
    desired_state: str
    observed_state: str
    browser_url: str | None = None
    internal_endpoint: str | None = None
    retention_policy: str
    last_error: str | None = None


class RuntimeStatusResponse(BaseModel):
    """
    用户侧 runtime 状态摘要。
    """

    runtime_id: str
    desired_state: str
    observed_state: str
    browser_url: str | None = None
    last_error: str | None = None


class RuntimeTaskResponse(BaseModel):
    """
    对应 GET /api/v1/runtime/tasks/{taskId} 响应。
    """

    task_id: str
    user_id: str
    runtime_id: str
    action: str
    status: str
    message: str | None = None


class RuntimeActionAcceptedResponse(BaseModel):
    """
    启动/停止/删除 runtime 的异步任务受理响应。
    """

    task_id: str
    action: str
    status: str

