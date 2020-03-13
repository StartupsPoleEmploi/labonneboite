def error_catcher(exception_class, value_on_error=None):
    """
    Decorator that catches NavitiaUnreachable exceptions. On error, it returns
    None.

    Usage:

        @error_catcher(ConnectionError, 42)
        def do_network_stuff():
            ...
    """

    def decorator(func):
        def decorated(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_class:
                return value_on_error

        return decorated

    return decorator


class BackendUnreachable(Exception):
    pass
