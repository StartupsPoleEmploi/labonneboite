import sys
from functools import reduce
from labonneboite.web.api import util
from flask import url_for

def add_security_params(_params):
    """
    Utility method that add `timestamp` and `signature` keys to _params.
    """
    timestamp = util.make_timestamp()
    signature = util.make_signature(_params, timestamp, user=_params.get('user'))
    _params['timestamp'] = timestamp
    _params['signature'] = signature
    return _params

def get2dict(acc, p):
    [key, val] = p.split('=')
    acc[key] = val
    return acc

def dict2get(_params):
    return lambda acc, key: acc + key + '=' + _params[key] + '&'

[inputUrl, urlGet] = sys.argv[1].split('?')
inputParams = reduce(get2dict, urlGet.split('&'), {})

params = add_security_params(inputParams)

url = inputUrl + '?' + reduce(dict2get(params), params.keys(), '')

print(url)
