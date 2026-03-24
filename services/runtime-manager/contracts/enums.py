from enum import Enum


class RetentionPolicy(str, Enum):
    PRESERVE_WORKSPACE = "preserve_workspace"
    WIPE_WORKSPACE = "wipe_workspace"


class ObservedState(str, Enum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DELETED = "deleted"
