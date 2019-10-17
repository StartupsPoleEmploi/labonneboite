from flask import current_app
from huey import RedisHuey
import redis

from labonneboite.conf import settings

from . import cache
from . import constants
from . import travel


def create_huey():
    """
    Huey is our asynchronous task scheduler.
    https://huey.readthedocs.io/en/latest/
    """
    if settings.PROCESS_ASYNC_TASKS:
        return RedisHuey(connection_pool=cache.RedisCache.connect().connection_pool)
    return DummyHuey()


class DummyHuey:
    """
    Dummy task scheduler that just trashes tasks. Useful for testing.
    """
    def task(self, *args, **kwargs):
        def patched(func):
            def dummy(*args, **kwargs):
                pass
            return dummy
        return patched


huey = create_huey()

# Asynchronous version of the `isochrone` function
isochrone = huey.task()(travel.isochrone)

def isochrones(location):
    """
    Compute isochrones asynchronously for all durations and modes. Each isochrone
    is computed in a separate task.
    """
    for mode in travel.TRAVEL_MODES:
        for duration in constants.ISOCHRONE_DURATIONS_MINUTES:
            try:
                isochrone(location, duration, mode=mode)
            except redis.ConnectionError as e:
                # Ignore redis connection errors -- precompute is temporarily
                # unavailable, deal with it
                current_app.logger.exception(e)
                return
