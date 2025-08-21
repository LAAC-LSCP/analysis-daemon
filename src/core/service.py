import time


class Service:
    """
    Main service object, runs the main loop of the program,
    stores configuration and interaction objects
    """

    def __init__(self, db_uow, http_client, config):
        self.db_uow = db_uow
        self.http_client = http_client
        self.config = config

    def main_loop(self):
        while True:
            self._tick()
            time.sleep(seconds=2.0)

    def _tick(self):
        raise NotImplementedError
