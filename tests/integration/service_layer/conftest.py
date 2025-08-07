from typing import Generator

import pytest

from src.service_layer import services


# TODO: duplication of code. See unit tests -> service_layer
# Don't want to place this further up just yet. Will get rid of this when we encapsulate
@pytest.fixture(autouse=True)
def reset_active_tasks() -> Generator[None]:
    # Clear before test
    services._active_tasks.clear()
    yield
    # Clear after test
    services._active_tasks.clear()
