def isochrone(origin, duration):
    """
    Undefined isochrone function.
    """
    return None

def durations(origin, destinations):
    """
    A dummy duration estimator that answers 'I don't know the durations' all
    the time.

    Returns: list of float durations, or None when duration could not be
    computed. The list has the same length as the destinations argument.
    """
    return [None]*len(destinations)

def directions(origin, destination):
    """
    Go in a straight line from origin to destination.

    Returns: list of coordinates
    """
    return [origin, destination]
