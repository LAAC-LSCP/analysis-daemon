from typing import Generator

import pytest

from src.service_layer import services


# TODO: code smell, should not have module-level state like that
# When ready, refactor service layer into separate class
@pytest.fixture(autouse=True)
def reset_active_tasks() -> Generator[None]:
    # Clear before test
    services._active_tasks.clear()
    yield
    # Clear after test
    services._active_tasks.clear()
