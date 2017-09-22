# coding: utf8

from urlparse import urlparse
import logging
import unicodedata
import urllib
import re

from flask import request, session
from flask_login import current_user

from labonneboite.conf import settings
from labonneboite.conf.common.contact_mode import CONTACT_MODE_DEFAULT
from labonneboite.common.load_data import load_contact_modes

logger = logging.getLogger('main')


def get_search_url(base_url, request_args, naf=None):
    query_string = {}
    if naf:
        query_string['naf'] = naf

    if request_args.get('q'):
        query_string['q'] = request_args.get('q').encode('utf8')
    if request_args.get('r'):
        query_string['r'] = request_args.get('r')
    if request_args.get('l'):
        query_string['l'] = request_args.get('l').encode('utf8')
    if request_args.get('d'):
        query_string['d'] = request_args.get('d')
    if request_args.get('lon'):
        query_string['lon'] = request_args.get('lon')
    if request_args.get('lat'):
        query_string['lat'] = request_args.get('lat')
    if request_args.get('j'):
        query_string['j'] = request_args.get('j').encode('utf8')
    if request_args.get('mode'):
        query_string['mode'] = request_args.get('mode')

    return "%s?%s" % (base_url, urllib.urlencode(query_string))


def get_user_ip():
    logger.debug("request.remote_addr = %s", request.remote_addr)
    logger.debug('request.headers.getlist("X-Forwarded-For") = %s', request.headers.getlist("X-Forwarded-For"))
    logger.debug("request.access_route = %s", request.access_route)
    # If a forwarded header exists, get its first ip (it's the client one),
    # otherwise, fallback to remote_addr.
    # http://werkzeug.pocoo.org/docs/0.10/wrappers/#werkzeug.wrappers.BaseRequest.access_route
    return request.access_route[0] if request.access_route else request.remote_addr


def user_is_pro():
    """
    The website has a special version called "Version PRO"
    which is only visible to "PRO users"

    PRO users are
    - Conseillers PE identified by their specific IP
    - Institutionals identified by their specific PEAM emails

    The "Version PRO" is the same as the regular "Version publique",
    plus some exclusive indicators, filters and data:
    - Flags : Junior, Senior, Handicap...
    - Office data : statistics about recruitments...
    """

    # Check user IP (not need to be authenticated)
    user_ip = get_user_ip()
    if user_ip in settings.VERSION_PRO_ALLOWED_IPS:
        return True

    # Check user e-mail by plain_value, suffix or regex (@see local_settings.py)
    if current_user.is_authenticated:
        current_user_email = current_user.email.lower()

        result = (current_user_email in settings.VERSION_PRO_ALLOWED_EMAILS
            or any(current_user_email.endswith(suffix) for suffix in settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES)
            or any(re.match(regexp, current_user_email) is not None for regexp in settings.VERSION_PRO_ALLOWED_EMAIL_REGEXPS)
            )

    return result

def pro_mode_activated():
    return session.get("pro_mode", False)


def get_doorbell_tags(tag):
    if tag not in ['faq', 'help', 'press', 'results']:
        raise Exception('unknown page')
    if user_is_pro():
        return ['conseiller', tag]
    return ['de', tag]


def get_hotjar_tag():
    if user_is_pro():
        return "conseiller"
    return "de"


def sanitize_string(s):
    if isinstance(s, str):
        return s.decode('utf-8')
    elif isinstance(s, unicode):
        return s
    raise Exception("not a string")


def is_safe_url(url, allowed_hosts=None):
    """
    Shamelessly ripped from Django:
    https://github.com/django/django/blob/13cd5b/django/utils/http.py#L347-L370
    """
    if not allowed_hosts:
        allowed_hosts = []
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
    # Forbid URLs that start with control characters. Some browsers (like
    # Chrome) ignore quite a few control characters at the start of a
    # URL and might consider the URL as scheme relative.
    if unicodedata.category(url[0])[0] == 'C':
        return False
    scheme = url_info.scheme
    # Consider URLs without a scheme (e.g. //example.com/p) to be http.
    if not url_info.scheme and url_info.netloc:
        scheme = 'http'
    valid_schemes = ['http', 'https']
    return ((not url_info.netloc or url_info.netloc in allowed_hosts) and (not scheme or scheme in valid_schemes))


def get_contact_mode_for_rome_and_naf(rome, naf):
    contact_mode_dict = load_contact_modes()
    naf_prefix = naf[:2]
    rome_to_contact_mode_dict = contact_mode_dict[naf_prefix]
    if rome in rome_to_contact_mode_dict:
        contact_mode = rome_to_contact_mode_dict[rome]
    elif rome_to_contact_mode_dict:
        contact_mode = rome_to_contact_mode_dict.values()[0]
    else:
        contact_mode = CONTACT_MODE_DEFAULT
    return contact_mode
