"""
The task manager lets you manually update tasks on the remote server

Useful to place a human in the loop, if something goes wrong
or for testing purposes
"""

import asyncio
from pathlib import Path
from typing import Optional

import click
from click import Context

from src.config.config import load_config
from src.core.exceptions import InValidTaskStatus
from src.core.response_types import PostPayload, Task
from src.core.types import UUID, Model, TaskStatus
from src.service_layer.http_client import HTTPClient


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
    http_client = _get_http_client(ctx.obj["config"])

    if id is not None:
        task = http_client.get_task_by_id(UUID(id))

        print(task)

        return

    if status is not None:
        if status not in TaskStatus:
            raise InValidTaskStatus(status)

        tasks = http_client.get_all_tasks_with_status(TaskStatus(status))

        for task in tasks:
            print(task)

        return

    tasks = http_client.get_all_tasks()

    for task in tasks:
        print(task)


@click.command()
@click.pass_context
def post(ctx: Context):
    """Put a task on the remote server"""
    config = ctx.obj["config"]
    http_client = _get_http_client(config)

    payload: PostPayload = {
        "analytics_uid_label": "",
        "uid_dataset": "",
        "kc_sub": "",
        "estimated_duration": 0,
    }

    task = http_client.post_task(payload)

    print(task)


# TODO: Below, isn't it more reasonable to define the task as it's defined on the
# network
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
    "--model",
    "-m",
    required=False,
    type=str,
    help="Model to be run",
)
@click.option(
    "--dataset-name",
    "-d",
    required=False,
    type=str,
    help="Dataset to run on",
)
def put(
    ctx: Context,
    id: str,
    owner: Optional[str] = None,
    status: Optional[str] = None,
    model: Optional[str] = None,
    dataset_name: Optional[str] = None,
):
    """Create a task on the remote server
    If any field is unspecified, it fills it with the from the already existing task
    """
    model_name: Optional[Model] = Model(model) if model else None
    owner_id: Optional[UUID] = UUID(owner) if owner else None
    task_status: Optional[TaskStatus] = TaskStatus(status) if status else None

    config = ctx.obj["config"]
    http_client = _get_http_client(config)

    existing_task = http_client.get_task_by_id(UUID(id))

    if not existing_task:
        raise ValueError(
            f"Task with UUID {id} does not exist. Did you mean to 'post' instead \
of 'put'?"
        )

    task = Task(
        datetime=existing_task.datetime,
        owner_id=owner_id or existing_task.owner_id,
        model_name=model_name or existing_task.model_name,
        dataset_name=dataset_name or existing_task.dataset_name,
        status=task_status or existing_task.status,
        id=UUID(id),
    )

    asyncio.run(_post_async(http_client, task))

    print(task)


async def _post_async(http_client: HTTPClient, task: Task):
    await http_client.put_task(task)


def _get_http_client(config: Path) -> HTTPClient:
    config_model = load_config(config)

    return HTTPClient(
        remote_api_url=str(config_model.http.base_url),
        client_id=config_model.http.client_id,
        client_secret=config_model.http.client_secret,
    )


task_manager.add_command(get)
task_manager.add_command(put)
task_manager.add_command(post)
