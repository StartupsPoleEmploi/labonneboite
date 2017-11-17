from labonneboite.conf import settings

def backend_name(function_name, mode):
    return settings.TRAVEL_VENDOR_BACKENDS[function_name][mode]

def backend(name):
    if name == 'dummy':
        from . import dummy as back
    elif name == 'datagouv':
        from . import datagouv as back
    elif name == 'google':
        from . import google as back
    elif name == 'graphhopper':
        from . import graphhopper as back
    elif name == 'ign':
        from . import ign as back
    elif name == 'navitia':
        from . import navitia as back
    else:
        raise ValueError('Invalid backend name: {}'.format(name))

    return back
