import time

from src.config.config import ConfigModel
from src.core.http_client import HTTPClient
from src.service_layer.publishing_uow import PublishingUoW


class Service:
    """
    Main service object, runs the main loop of the program,
    stores configuration and interaction objects
    """

    def __init__(
        self, uow: PublishingUoW, http_client: HTTPClient, config: ConfigModel
    ):
        self.uow = uow
        self.http_client = http_client
        self.config = config

    def main_loop(self):
        while True:
            self._tick()
            time.sleep(seconds=2.0)

    def _tick(self):
        raise NotImplementedError
