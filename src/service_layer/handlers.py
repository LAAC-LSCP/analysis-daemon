from src.domain.events import TaskCompleted, TaskCreated, TaskFailed, TaskStarted
from src.domain.model import Task
from src.service_layer.publishing_uow import PublishingUoW


def handle_start_task(_: TaskStarted, __: PublishingUoW) -> None:
    raise NotImplementedError


def handle_failed_task(_: TaskFailed, __: PublishingUoW) -> None:
    raise NotImplementedError


def handle_create_task(
    event: TaskCreated,
    uow: PublishingUoW,
) -> None:
    task = Task(
        _id=event.task_id,
        owner_id=event.owner_id,
        filesystem=event.filesystem,
        model=event.model,
        script_path=event.script_path,
    )

    with uow:
        uow.tasks.save(task)

        uow.commit()


def handle_complete_task(
    event: TaskCompleted,
    uow: PublishingUoW,
) -> None:
    with uow:
        task = uow.tasks.get(event.task_id)

        if not task:
            return

        if task.completed:
            return

        uow.tasks.save(task)

        uow.commit()


def handle_run_task(
    event: TaskStarted,
    uow: PublishingUoW,
) -> None:
    task = uow.tasks.get(event.task_id)

    if not task:
        return

    if task.running:
        return

    uow.tasks.save(task)

    uow.commit()
