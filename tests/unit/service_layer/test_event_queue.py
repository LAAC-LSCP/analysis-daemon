from src.core.types import UUID
from src.domain.events import TaskCreated
from src.service_layer.queue.event_queue import EventQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fake_handlers import FakeHandlers


def test_command_queue_priority():
    uow = PublishingUoW(FakeUoW())
    fake_handlers: FakeHandlers = FakeHandlers(uow)
    queue = EventQueue(uow=uow, handlers=fake_handlers)

    event = TaskCreated(
        task_id=UUID("1"),
    )

    assert queue._get_priority(event) == 1
