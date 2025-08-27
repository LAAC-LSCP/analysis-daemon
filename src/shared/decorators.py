import logging


def catch_and_log_exception(exception=Exception, logger=logging.getLogger(__name__)):
    def deco(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except exception as err:
                logger.exception(err)
            else:
                return result

        return wrapper

    return deco
