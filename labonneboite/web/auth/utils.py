from urllib.parse import urlencode

from flask import request, url_for

from labonneboite.conf import settings


def login_url(next_url=None):
    querystring = {
        # This argument tells flask-login that the authentication user id
        # should be persisted in a cookie
        settings.REMEMBER_ME_ARG_NAME: "1"
    }
    next_url = next_url or (request.url if request else None)
    if next_url:
        querystring["next"] = next_url
    return url_for("social.auth", backend="peam-openidconnect") + "?" + urlencode(querystring)
