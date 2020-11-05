
import logging
import json

from .constants import DEFAULT_TRAVEL_MODE, TRAVEL_MODES
from . import exceptions
from . import vendors

logger = logging.getLogger(__name__)


# Note: everywhere we deal with coordinates, they are assumed to be float tuples of the
# form (latitude, longitude).

def isochrone(location, duration, mode=None):
    """
    Compute the isochrone around a given location.

    Args:
        origin (coordinates)
        duration (integer): size of the isochrone, in minutes.
        mode (str)

    Return:
        A list of polygons; each polygon is itself a list of coordinates. Thus,
        the result is a list of list of coordinates.
    """
    return backend_func('isochrone', mode, location, duration)


def durations(origin, destinations, mode=None):
    """
    Compute the travel durations from one origin to multiple destinations.

    Args:
        origin (coordinates)
        destinations (list of coordinates)
        mode (str)

    Return:
        A list of float values of the same length as `destinations`. Whenever a
        duration could not be computed, None is returned instead.
    """
    backend_name, mode = backend_info('durations', mode)
    func_name = 'durations'

    backend = vendors.backend(backend_name)
    # Compute durations
    try:
        computed = backend.durations(origin, destinations)
    except exceptions.BackendUnreachable:
        computed = [None] * len(destinations)

    return computed


def backend_func(func_name, mode, *args):
    """
    Load the appropriate backend and run a given function from this backend.

    Args:
        mode (str): travel mode, one of TRAVEL_MODES or None
        *args: remaining arguments will be passed to the backend function. They
    """
    backend = vendors.backend(backend_name)
    backend_func = getattr(backend, func_name)
    try:
        result = backend_func(*args)
    except exceptions.BackendUnreachable:
        result = None

    return result


def backend_info(func_name, mode):
    """
    Return:

        backend_name (str)
        mode (str)
    """
    mode = mode or DEFAULT_TRAVEL_MODE
    if mode not in TRAVEL_MODES:
        raise ValueError('Invalid travel mode: {}'.format(mode))
    backend_name = vendors.backend_name(func_name, mode)
    return backend_name, mode

