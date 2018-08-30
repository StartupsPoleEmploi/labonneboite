# coding: utf8

from urllib.parse import urlencode

from flask import Blueprint, redirect, session, url_for, render_template
from flask_login import current_user, logout_user

from labonneboite.common.models import get_user_social_auth
from labonneboite.conf import settings
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect


authBlueprint = Blueprint('auth', __name__)


@authBlueprint.route('/logout')
def logout(user_social_auth=None):
    """
    Log a user out.

    Param `user_social_auth`: a `UserSocialAuth` instance. `None` most of the time, except when a user
    is coming from the `user.account_delete` view. This param is intended to be passed when the view
    is called directly as a Python function, i.e. not with a `redirect()`.
    """
    if not current_user.is_authenticated:
        return redirect(url_for('root.home'))

    logged_with_peam = session.get('social_auth_last_login_backend') == PEAMOpenIdConnect.name
    if logged_with_peam and not user_social_auth:
        user_social_auth = get_user_social_auth(current_user.id)

    # Log the user out and destroy the LBB session.
    logout_user()

    # Clean the session: drop Python Social Auth info because it isn't done by `logout_user`.
    if 'social_auth_last_login_backend' in session:
        # Some backends have a `backend-name_state` stored in session as required by e.g. Oauth2.
        social_auth_state_key = '%s_state' % session['social_auth_last_login_backend']
        if social_auth_state_key in session:
            session.pop(social_auth_state_key)
        session.pop('social_auth_last_login_backend')

    # Log the user out from PEAM and destroy the PEAM session.
    if logged_with_peam and user_social_auth:
        params = {
            'id_token_hint': user_social_auth.extra_data['id_token'],
            'redirect_uri': url_for('auth.logout_from_peam_callback', _external=True),
        }
        peam_logout_url = '%s/compte/deconnexion?%s' % (settings.PEAM_AUTH_BASE_URL, urlencode(params))
        # After this redirect, the user will be redirected to the LBB website `logout_from_peam_callback` route.
        return redirect(peam_logout_url)

    return redirect(url_for('root.home'))


@authBlueprint.route('/logout/peam/callback')
def logout_from_peam_callback():
    """
    The route where a user is redirected after a log out through the PEAM website.
    """
    return redirect(url_for('root.home'))

@authBlueprint.route('/iframe')
def iframe():
    return render_template("auth/iframe.html") if current_user.is_authenticated else ""
