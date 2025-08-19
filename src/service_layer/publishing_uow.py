from src.adapters.tracking_repository import TrackingRepository
from src.service_layer import message_bus
from src.service_layer.uow import AbstractUoW


class PublishingUoW(AbstractUoW[TrackingRepository]):
    """
    Decorator for unit of work to allow it to publish events
    """

    _uow: AbstractUoW[TrackingRepository]

    @property
    def tasks(self) -> TrackingRepository:
        return self._uow.tasks

    @tasks.setter
    def tasks(self, value: TrackingRepository) -> None:
        self._uow.tasks = value

    def __init__(self, uow: AbstractUoW):
        self._uow = uow

    def __enter__(self):
        self._uow.__enter__()

    def __exit__(self, *args):
        self._uow.__exit__(*args)

    def rollback(self):
        self._uow.rollback()

    def commit(self) -> None:
        self._uow.commit()
        self.publish_events()

    def publish_events(self) -> None:
        for task in self._uow.tasks.seen:
            while task.events:
                event = task.events.pop(0)
                message_bus.handle(event)
