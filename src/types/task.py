from typing import Literal, Union
from .tasks import LogArgs, LogTaskName

TaskType = Literal[LogTaskName]
TaskArgs = Union[LogArgs]
