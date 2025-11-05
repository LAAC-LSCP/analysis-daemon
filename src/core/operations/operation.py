from dataclasses import dataclass
from pathlib import Path

from src.config.config import ConfigModel
from src.core.exceptions import NoScriptWithOperation

from ..types import OperationName as OperationStr
from ..types import ScriptArgs, ScriptFlags


@dataclass
class Operation:
    operation: OperationStr
    script_path: Path
    args: ScriptArgs
    flags: ScriptFlags


def operation_factory(
    operation: OperationStr,
    config: ConfigModel,
    args: ScriptArgs = {},
    flags: ScriptFlags = [],
) -> Operation:
    script_path: Path | None = next(
        (
            script.path
            for script in config.scripts
            if script.model_name == operation.value
        ),
        None,
    )

    if script_path is None:
        raise NoScriptWithOperation(operation)

    return Operation(
        operation=operation,
        script_path=script_path,
        args=get_args_for_op(operation, args),
        flags=get_flags_for_op(operation, flags),
    )


def get_args_for_op(_: OperationStr, args: ScriptArgs = {}) -> ScriptArgs:
    # TODO: Fill this in later.
    # This function will remove args that should not be there
    # And add args that might be missing

    return args


def get_flags_for_op(_: OperationStr, flags: ScriptFlags = []) -> ScriptFlags:
    # TODO: Fill this in later.
    # This function will remove flags that should not be there
    # And add flags that might be missing

    return flags
