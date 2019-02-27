# coding: utf8

"""
Note: everywhere we deal with coordinates, they are assumed to be float tuples
of the form (latitude, longitude).
"""

import logging

from .cache import Cache
from .constants import DEFAULT_TRAVEL_MODE, TRAVEL_MODES
from . import exceptions
from . import vendors

logger = logging.getLogger(__name__)


ISOCHRONE_CACHE = Cache()
DIRECTIONS_CACHE = Cache()
DURATIONS_CACHE = Cache()


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
    return backend_cached_func(ISOCHRONE_CACHE, 'isochrone', mode, location, duration)


def directions(origin, destination, mode=None):
    """
    Compute the coordinates of the travel line between origin and destination.

    Args:
        origin (coordinates)
        destination (coordinates)
        mode (str)

    Return:
        A list of coordinates that represents the travel line
    """
    return backend_cached_func(DIRECTIONS_CACHE, 'directions', mode, origin, destination)


def durations(origin, destinations, mode=None):
    """
    Compute the travel durations from one origin to multiple destinations.

    This function works a little different from `directions` and `isochrone`
    because we do not want to cache a list of result. Instead, we want to cache
    each result individually.

    Args:
        origin (coordinates)
        destinations (list of coordinates)
        mode (str)

    Return:
        A list of float values of the same length as `destinations`. Whenever a
        duration could not be computed, None is returned instead.
    """
    durations_by_destination = {}
    destinations_to_fetch = []

    backend_name, mode = backend_info('durations', mode)
    func_name = 'durations'

    # Fetch results from cache
    for destination in set(destinations):
        key = cache_key(backend_name, func_name, mode, origin, destination)
        duration = DURATIONS_CACHE.get(key, -1)
        if duration == -1:
            destinations_to_fetch.append(destination)
            duration = None
        durations_by_destination[destination] = duration

    # Fetch other results
    if destinations_to_fetch:
        backend = vendors.backend(backend_name)
        # Compute durations
        try:
            computed = backend.durations(origin, destinations_to_fetch)
        except exceptions.BackendUnreachable:
            computed = [None] * len(destinations_to_fetch)

        # Store in cache
        for destination, duration in zip(destinations_to_fetch, computed):
            if duration is not None:
                key = cache_key(backend_name, func_name, mode, origin, destination)
                DURATIONS_CACHE.set(key, duration)
            durations_by_destination[destination] = duration

    return [durations_by_destination.get(destination) for destination in destinations]


def backend_cached_func(cache, func_name, mode, *args):
    """
    Load the appropriate backend and run a given function from this backend.
    The function is only run if the result is not already present in the cache.
    Then, store the result in the cache.

    Args:
        cache (Cache)
        func_name (str): name of the backend function to run
        mode (str): travel mode, one of TRAVEL_MODES or None
        *args: remaining arguments will be passed to the backend function. They
        will also be used to compute the cache key.
    """
    backend_name, mode = backend_info(func_name, mode)
    key = cache_key(backend_name, func_name, mode, *args)

    # Load from cache
    result = cache.get(key, None)
    if result is not None:
        return result

    # Compute result
    backend = vendors.backend(backend_name)
    backend_func = getattr(backend, func_name)
    try:
        result = backend_func(*args)
    except exceptions.BackendUnreachable:
        result = None

    # Note that we could store in cache the fact that the value could not be
    # computed. In that case, we may not want to try recompute the same value
    # right away. For instance, we could store 'DID_NOT_COMPUTE' in the cache.
    # We need to observe the behaviour in production first; otherwise, we may
    # accidentally set all values to DID_NOT_COMPUTE in case of temporary
    # unavailability.
    if result is not None:
        # Store result in cache
        cache.set(key, result)

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


def cache_key(backend_name, func_name, mode, *args):
    """
    Compute the key used to store the result of the backend function to which
    *args will be passed.
    """
    return tuple([backend_name, func_name, mode] + list(args))
