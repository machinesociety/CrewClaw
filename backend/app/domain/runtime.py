from dataclasses import dataclass
from enum import Enum

from app.domain.users import DesiredState, ObservedState


class RuntimeAction(str, Enum):
    ENSURE_RUNNING = "ensure_running"
    STOP = "stop"
    DELETE = "delete"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class RuntimeTask:
    """
    runtime 启停删除等异步任务。

    TODO:
    - 增加创建时间、完成时间等字段，便于排障。
    - 在仓储层实现状态迁移持久化。
    """

    task_id: str
    user_id: str
    runtime_id: str
    action: RuntimeAction
    status: TaskStatus
    message: str | None = None


@dataclass
class RuntimeStateView:
    """
    用于前台展示的 runtime 状态汇总视图。
    """

    runtime_id: str
    desired_state: DesiredState
    observed_state: ObservedState
    browser_url: str | None = None
    last_error: str | None = None

