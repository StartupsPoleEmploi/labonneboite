import ipaddress
from enum import Enum
from typing import Callable, Type, Optional, Any, Iterable, Collection, TYPE_CHECKING, Union, Dict, TypeVar
from urllib.parse import urlparse
import logging
from functools import wraps
from time import time
from ipaddress import IPv4Address, IPv6Address

from flask import request

from labonneboite.common.contact_mode import CONTACT_MODE_DEFAULT
from labonneboite.common.load_data import load_contact_modes
from labonneboite.common.conf import settings

if TYPE_CHECKING:
    from labonneboite_common.models.office_mixin import OfficeMixin

T_co = TypeVar('T_co', covariant=True)
logger = logging.getLogger('main')


def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrap(*args: Any, **kw: Any) -> Any:
        ts = time()
        result = func(*args, **kw)
        te = time()
        duration = te - ts
        # anything under 1sec is not worth polluting the logs
        if settings.ENABLE_TIMEIT_TIMERS and duration >= 1.0:
            msg = 'func:%r - took: %2.4f sec - args:[%r, %r] ' % \
                  (func.__name__, duration, args, kw)
            msg = msg[:200]  # cut if msg too long
            logger.info(msg)
            # print messages are displayed all at once when the job ends in jenkins console output
            print(msg)
        return result

    return wrap


def get_user_ip() -> Optional[Union[IPv4Address, IPv6Address]]:
    """
    Return the current user_ip as an ipaddress.IPv4Address object.
    """
    logger.debug("request.remote_addr = %s", request.remote_addr)
    logger.debug('request.headers.getlist("X-Forwarded-For") = %s', request.headers.getlist("X-Forwarded-For"))
    logger.debug("request.access_route = %s", request.access_route)
    # If a forwarded header exists, get its first ip (it's the client one),
    # otherwise, fallback to remote_addr.
    # http://werkzeug.pocoo.org/docs/0.10/wrappers/#werkzeug.wrappers.BaseRequest.access_route
    ip = request.access_route[0] if request.access_route else request.remote_addr
    return ipaddress.ip_address(ip) if ip else None  # type: ignore


def is_decoded_url_safe(url: str) -> bool:
    """
    Ripped and adapted from Django:
    https://github.com/django/django/blob/13cd5b/django/utils/http.py#L347-L370
    """
    # Chrome considers any URL with more than two slashes to be absolute, but
    # urlparse is not so flexible. Treat any url with three slashes as unsafe.
    if url.startswith('///'):
        return False

    url_info = urlparse(url)

    # Forbid URLs like http:///example.com - with a scheme, but without a hostname.
    # In that URL, example.com is not the hostname but, a path component. However,
    # Chrome will still consider example.com to be the hostname, so we must not
    # allow this syntax.
    if not url_info.netloc and url_info.scheme:
        return False

    # Allow only relative URLs without host e.g. '/entreprises?j=Boucherie[...]'
    return not url_info.netloc and not url_info.scheme


def get_contact_mode_for_rome_and_office(rome: str, office: 'OfficeMixin') -> str:
    if office.contact_mode:
        return office.contact_mode

    naf_prefix = office.naf[:2]
    naf_prefix_to_rome_to_contact_mode: Dict[str, Dict[str, str]] = load_contact_modes()
    try:
        return naf_prefix_to_rome_to_contact_mode[naf_prefix][rome]
    except KeyError:
        pass
    try:
        return list(naf_prefix_to_rome_to_contact_mode[naf_prefix].values())[0]
    except (KeyError, IndexError):
        return CONTACT_MODE_DEFAULT


def unique_elements(iterable: Iterable[T_co], key: Optional[Callable[[T_co], Any]] = None) -> Collection[T_co]:
    """
    Filter elements from an iterable so that only unique items are preserved.
    This supports some non-hashable values, such as dict or lists.

    Args:
        iterable
        key (func): function to be applied to each element to determine
        unicity. If undefined, it is the identity function.
    """
    seen = set()
    result = []
    for element in iterable:
        hashed = element if key is None else key(element)
        if isinstance(hashed, dict):
            hashed = tuple(sorted(hashed.items()))
        elif isinstance(hashed, list):
            hashed = tuple(hashed)
        if hashed not in seen:
            result.append(element)
            seen.add(hashed)
    return result


def get_enum_from_value(EnumClass: Type[Enum], value: str, default: Optional[Any] = None) -> Any:
    '''
    Get an enum member out of a string value, e.g. Color.BLUE out of 1 if Color.BLUE.value is 1
    Used to convert value in GET to enum
    '''
    try:
        return EnumClass(value)
    except ValueError:
        return default
