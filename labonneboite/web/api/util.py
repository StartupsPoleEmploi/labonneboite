import datetime
import hmac
import urllib.request
import urllib.parse
import urllib.error
import hashlib
from labonneboite.conf import settings


class TimestampFormatException(Exception):
    pass


class TimestampExpiredException(Exception):
    pass


class InvalidSignatureException(Exception):
    pass


class UnknownUserException(Exception):
    pass


def make_timestamp():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    return timestamp


def get_ordered_argument_string(args):
    args_copy = dict(args)
    if 'signature' in args_copy:
        del args_copy['signature']
    ordered_args = []
    for arg in sorted(args_copy):
        ordered_args.append((arg, args_copy[arg]))
    return urllib.parse.urlencode(ordered_args)


def make_signature(args, timestamp, user='labonneboite'):
    args['timestamp'] = timestamp
    api_key = get_key(user, '')
    return compute_signature(args, api_key)


def check_api_request(request):
    user = request.args['user']
    api_key = get_key(user)
    if api_key is None:
        raise UnknownUserException

    timestamp = request.args.get('timestamp')
    try:
        timestamp_dt = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
    except Exception as e:
        print(e, flush=True)
        raise TimestampFormatException("incorrect format")
    # check timestamp for API request and reject it if it's too old or in the future
    # needs a correctly UTC calibrated time here, for now it works because timestamps are computed on the same server
    # for API request creation and API request checking
    now = datetime.datetime.utcnow()
    seconds = (now - timestamp_dt).total_seconds()
    if abs(seconds) > 60 * 10:
        raise TimestampExpiredException("time window is over")
    check_signature(request, request.args.get('signature'), api_key)


def compute_signature(args, api_key):
    ordered_arg_string = get_ordered_argument_string(args)
    return hmac.new(api_key.encode(), ordered_arg_string.encode(), hashlib.sha256).hexdigest()


def check_signature(request, requested_signature, api_key):
    args = {}
    for k, v in request.args.items():
        # unicode parameters (e.g. rome_codes_keyword_search) need to be properly encoded
        args[k] = v.encode('utf8')
    computed_signature = compute_signature(args, api_key)
    if not computed_signature == requested_signature:
        raise InvalidSignatureException


def has_scope(api_user_name, api_user_name_forwarded, scope):
    user_data = settings.API_USERS.get(api_user_name_forwarded, settings.API_USERS.get(api_user_name))
    if user_data is None:
        return False
    return scope in user_data.get('scopes', [])


def get_key(api_user_name, default=None):
    return settings.API_KEYS.get(api_user_name, default)
