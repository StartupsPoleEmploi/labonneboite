import re
import ipaddress

from flask import session, request
from flask_login import current_user

from labonneboite.conf import settings
from .util import get_user_ip


PRO_VERSION_SESSION_KEY = 'pro_version'


def ips_from_ip_ranges(ip_ranges):
    """
    Return a list of IP addresses from a list of IP ranges.

    Usage example:
        ips_from_ip_ranges(['192.168.0.0', '192.168.0.0/22'])

    Input:
        ip_ranges: list of strings

    Output:
        list of ipaddress.IPv4Address objects

    """
    ips = []

    for ip_range in ip_ranges:
        for ip in ipaddress.IPv4Network(ip_range):
            ips.append(ip)

    return ips



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

    # Check user IP (no need to be authenticated)
    user_ip = get_user_ip()
    user_agent = request.headers.get('User-Agent')

    whitelisted_ips = ips_from_ip_ranges(settings.VERSION_PRO_ALLOWED_IPS)

    if user_ip in whitelisted_ips and 'Pila' not in user_agent:
        return True

    # Check user e-mail by plain_value, suffix or regex (@see local_settings.py)
    if current_user.is_authenticated:
        current_user_email = current_user.email.lower()

        return (current_user_email in settings.VERSION_PRO_ALLOWED_EMAILS
            or any(current_user_email.endswith(suffix) for suffix in settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES)
            or any(re.match(
                regexp, current_user_email) is not None for regexp in settings.VERSION_PRO_ALLOWED_EMAIL_REGEXPS))

    return False

def pro_version_enabled():
    if not user_is_pro() and PRO_VERSION_SESSION_KEY in session:
        session.pop(PRO_VERSION_SESSION_KEY)
    return session.get(PRO_VERSION_SESSION_KEY, False)

def toggle_pro_version():
    if pro_version_enabled():
        session.pop(PRO_VERSION_SESSION_KEY)
    else:
        session[PRO_VERSION_SESSION_KEY] = True
