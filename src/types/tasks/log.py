from dataclasses import dataclass
from typing import Literal

LogTaskName = Literal["log"]


@dataclass
class LogArgs:
    text: list[str]
