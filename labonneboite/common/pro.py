# coding: utf8
import re

from flask import session
from flask_login import current_user

from labonneboite.conf import settings
from .util import get_user_ip


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
    if user_ip in settings.VERSION_PRO_ALLOWED_IPS:
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
    if not user_is_pro() and 'pro_version' in session:
        session.pop('pro_version')
    return session.get('pro_version', False)
