from pydantic import HttpUrl

from src.core.response_types import EcholaliaResponse


class HTTPClient:
    def __init__(self, _: HttpUrl):
        pass

    async def call_endpoint(self) -> EcholaliaResponse:
        raise NotImplementedError
