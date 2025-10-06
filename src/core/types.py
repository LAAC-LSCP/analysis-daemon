from enum import StrEnum
from typing import NewType

UUID = NewType("UUID", str)


class TaskType(StrEnum):
    SCRIPT = "script"
    MODEL = "model"
    UNKNOWN = "unknown"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class Model(StrEnum):
    VTC = "vtc"
    ALICE = "alice"
    VCM = "vcm"
    UNKNOWN = "unknown"
