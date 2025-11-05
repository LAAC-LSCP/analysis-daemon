from enum import StrEnum
from typing import Any, Dict, List, NewType

UUID = NewType("UUID", str)
ScriptArgs = Dict[str, Any | None]
ScriptFlags = List[str]


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OperationName(StrEnum):
    VTC = "vtc"
    ALICE = "alice"
    VCM = "vcm"
    VTC2 = "vtc-2.0"
    W2V2_SMD = "w2v2-smd"
    ACOUSTICS = "acoustics"
    RESTRICTIVE = "derive-restrictive"
    CVA = "derive-cva"
    CONVERSATIONS = "derive-conversations"
