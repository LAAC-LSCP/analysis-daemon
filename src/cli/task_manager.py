"""
The task manager lets you manually update tasks on the remote server

Useful to place a human in the loop, if something goes wrong
or for testing purposes
"""

from pathlib import Path
from typing import Optional, Tuple

import click
from click import Context

from src.config.config import load_config
from src.core.types import UUID, Operation, TaskStatus
from src.service_layer.bootstrap import get_http_client
from src.service_layer.task_manager.task_manager import TaskManager


@click.group()
@click.pass_context
def task_manager(ctx: Context):
    """Manage echolalia tasks on the real server

    (based on the configuration file)"""
    pass


@click.command()
@click.option(
    "--id",
    "-i",
    required=False,
    type=str,
    help="Task UUID. If not specified gets all tasks. \
        Takes precedence over task status",
)
@click.option(
    "--status",
    "-s",
    required=False,
    type=str,
    help="Task status. If not specified does not filter by status",
)
@click.pass_context
def get(ctx: Context, id: Optional[str], status: Optional[str]):
    """Prints tasks received from the Echolalia server"""
    http_client = get_http_client(load_config(ctx.obj["config"]))
    task_manager = TaskManager(http_client)
    tasks = task_manager.get(
        id=UUID(id) if id else None, status=TaskStatus(status) if status else None
    )

    for task in tasks:
        print(task)


@click.command()
@click.pass_context
@click.option(
    "--analytics-uuid-label",
    "-a",
    required=True,
    type=str,
    help="Analytics label UUID",
)
@click.option(
    "--dataset-uuid",
    "-d",
    required=True,
    type=str,
    help="Dataset uuid",
)
def post(ctx: Context, analytics_uuid_label: str, dataset_uuid: str):
    """Put a task on the remote server and prints it"""
    http_client = get_http_client(load_config(ctx.obj["config"]))
    task_manager = TaskManager(http_client)
    task = task_manager.post(
        analytics_uuid_label=UUID(analytics_uuid_label), dataset_uuid=UUID(dataset_uuid)
    )

    print(task)


@click.command()
@click.pass_context
@click.option(
    "--id",
    "-i",
    required=True,
    type=str,
    help="Task UUID",
)
@click.option(
    "--input-folder",
    "-f",
    required=True,
    type=click.Path(exists=True),
    help="Input folder path",
)
@click.option(
    "--owner",
    "-o",
    required=False,
    type=str,
    help="Owner UUID",
)
@click.option(
    "--status",
    "-s",
    required=False,
    type=str,
    help="Task status",
)
@click.option(
    "--operation",
    "-m",
    required=False,
    type=str,
    help="Operation to be run",
)
@click.option(
    "--dataset-name",
    "-d",
    required=False,
    type=str,
    help="Dataset to run on",
)
@click.option(
    "--input",
    required=False,
    multiple=True,
    type=click.Path(exists=True),
    help="Input file (can be used multiple times)",
)
def put(
    ctx: Context,
    id: str,
    input_folder: str,
    owner: Optional[str] = None,
    status: Optional[str] = None,
    operation: Optional[str] = None,
    dataset_name: Optional[str] = None,
    input: Tuple[str] = (),  # type: ignore
):
    """Create a task on the remote server
    If any field is unspecified, it fills it with the from the already existing task
    """
    http_client = get_http_client(load_config(ctx.obj["config"]))
    task_manager = TaskManager(http_client)
    task = task_manager.put(
        id=UUID(id),
        input_folder=Path(input_folder),
        owner_id=UUID(owner) if owner else None,
        task_status=TaskStatus(status) if status else None,
        operation=Operation(operation) if operation else None,
        dataset_name=dataset_name,
        inputs=[Path(i) for i in input],
    )

    print(task)


task_manager.add_command(get)
task_manager.add_command(put)
task_manager.add_command(post)
