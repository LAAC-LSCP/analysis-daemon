from src.domain.events import TaskCompleted, TaskCreated, TaskStarted
from src.domain.model import Task
from src.service_layer.publishing_uow import PublishingUoW


def add_task(
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


def mark_task_complete(
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


def mark_task_running(
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
