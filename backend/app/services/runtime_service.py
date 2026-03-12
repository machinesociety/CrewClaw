from app.domain.runtime import RuntimeTask, RuntimeAction, TaskStatus


class RuntimeService:
    """
    runtime 编排服务。

    TODO:
    - 读取 UserRuntimeBinding 与模型配置，组装启动模板。
    - 调用 runtime-manager 客户端执行 ensure_running/stop/delete。
    - 将任务状态持久化到任务仓储。
    """

    def ensure_running(self, user_id: str) -> RuntimeTask:
        _ = user_id
        return RuntimeTask(
            task_id="rtask_001",
            user_id="u_001",
            runtime_id="rt_001",
            action=RuntimeAction.ENSURE_RUNNING,
            status=TaskStatus.PENDING,
            message="accepted",
        )

    def stop_runtime(self, user_id: str) -> RuntimeTask:
        _ = user_id
        return RuntimeTask(
            task_id="rtask_002",
            user_id="u_001",
            runtime_id="rt_001",
            action=RuntimeAction.STOP,
            status=TaskStatus.PENDING,
            message="accepted",
        )

    def delete_runtime(self, user_id: str) -> RuntimeTask:
        _ = user_id
        return RuntimeTask(
            task_id="rtask_003",
            user_id="u_001",
            runtime_id="rt_001",
            action=RuntimeAction.DELETE,
            status=TaskStatus.PENDING,
            message="accepted",
        )

