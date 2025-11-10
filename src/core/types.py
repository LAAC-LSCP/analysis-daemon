from enum import StrEnum
from typing import NewType

UUID = NewType("UUID", str)


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Operation(StrEnum):
    VTC = "vtc"
    ALICE = "alice"
    VCM = "vcm"
    ACOUSTICS = "acoustics"
    W2V2 = "w2v2"
