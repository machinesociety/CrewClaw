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

    @property
    def is_terminal(self) -> bool:
        return self in {
            TaskStatus.SUCCEEDED,
            TaskStatus.FAILED,
            TaskStatus.CANCELED,
        }


@dataclass
class RuntimeTask:
    """
    runtime 启停删除等异步任务。

    目前仅在内存中管理状态迁移，后续可以接入持久化仓储。
    """

    task_id: str
    user_id: str
    runtime_id: str
    action: RuntimeAction
    status: TaskStatus
    message: str | None = None

    def start(self, message: str | None = None) -> None:
        if self.status != TaskStatus.PENDING:
            return
        self.status = TaskStatus.RUNNING
        if message is not None:
            self.message = message

    def succeed(self, message: str | None = None) -> None:
        if self.status not in {TaskStatus.PENDING, TaskStatus.RUNNING}:
            return
        self.status = TaskStatus.SUCCEEDED
        if message is not None:
            self.message = message

    def fail(self, message: str | None = None) -> None:
        if self.status.is_terminal:
            return
        self.status = TaskStatus.FAILED
        if message is not None:
            self.message = message

    def cancel(self, message: str | None = None) -> None:
        if self.status.is_terminal:
            return
        self.status = TaskStatus.CANCELED
        if message is not None:
            self.message = message


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

