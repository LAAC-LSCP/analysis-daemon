from src.domain.commands import CompleteTask, CreateTask, RunTask
from src.domain.events import Event
from src.domain.model import Task
from src.service_layer.publishing_uow import PublishingUoW


def handle_not_implemented(_: Event, __: PublishingUoW) -> None:
    raise NotImplementedError


def handle_create_task(
    command: CreateTask,
    uow: PublishingUoW,
) -> None:
    task = Task(
        _id=command.task_id,
        owner_id=command.owner_id,
        filesystem=command.filesystem,
        model=command.model,
        script_path=command.script_path,
    )

    with uow:
        uow.tasks.save(task)

        uow.commit()


def handle_complete_task(
    command: CompleteTask,
    uow: PublishingUoW,
) -> None:
    with uow:
        task = uow.tasks.get(command.task_id)

        if not task:
            return

        if task.completed:
            return

        uow.tasks.save(task)

        uow.commit()


def handle_run_task(
    command: RunTask,
    uow: PublishingUoW,
) -> None:
    task = uow.tasks.get(command.task_id)

    if not task:
        return

    if task.running:
        return

    uow.tasks.save(task)

    uow.commit()
