from labonneboite.conf import settings


def backend_name(function_name, mode):
    return settings.TRAVEL_VENDOR_BACKENDS[function_name][mode]


def backend(name):
    if name == "dummy":
        from . import dummy as back
    elif name == "ign":
        from . import ign as back
    elif name == "navitia":
        from . import navitia as back
    elif name == "ign_mock":
        from .mocks import ign as back
    elif name == "navitia_mock":
        from .mocks import navitia as back
    else:
        raise ValueError("Invalid backend name: {}".format(name))

    return back
