import logging
from typing import Any, Optional


def catch_and_log_exception(
    exception=Exception,
    logger=logging.getLogger(__name__),
    default_return: Optional[Any] = None,
    context_message: Optional[str] = None,
):
    def deco(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except exception as err:
                if context_message:
                    logger.exception(f"{context_message}: {err}")
                else:
                    logger.exception(err)

                return default_return
            else:
                return result

        return wrapper

    return deco
