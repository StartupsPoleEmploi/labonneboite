import logging
import string
import random
from urllib.parse import urlencode

from flask import Blueprint, flash, redirect, session, url_for, render_template, request
from flask_login import current_user, logout_user

from labonneboite.common import activity
from labonneboite.common.models import get_user_social_auth
from labonneboite.conf import settings
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect
from labonneboite.web.auth.backends.peam_recruiter import SessionKeys
from labonneboite.web.auth.backends.peam_recruiter import get_token_data, get_recruiter_data, PeamRecruiterError, PeamRecruiterLoginCancelled
from labonneboite.web.search.forms import CompanySearchForm
from labonneboite.web.utils import fix_csrf_session


authBlueprint = Blueprint('auth', __name__)

logger = logging.getLogger('main')

def random_string(length=10):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


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

    logged_with_peam = session.get(
        'social_auth_last_login_backend') == PEAMOpenIdConnect.name
    if logged_with_peam and not user_social_auth:
        user_social_auth = get_user_social_auth(current_user.id)

    # Log the user out and destroy the LBB session.
    activity.log('deconnexion')
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
        peam_logout_url = '%s/compte/deconnexion?%s' % (
            settings.PEAM_AUTH_BASE_URL, urlencode(params))
        # After this redirect, the user will be redirected to the LBB website `logout_from_peam_callback` route.
        return redirect(peam_logout_url)

    return redirect(url_for('root.home'))


@authBlueprint.route('/logout/peam/callback')
def logout_from_peam_callback():
    """
    The route where a user is redirected after a log out through the PEAM website.
    """

    # Quick ugly but useful fix
    referer = request.referrer
    if referer and len(referer) > 1700:
        # If the referer is too long, the redirect will return a 502 status code.
        # I did not find how to change the referrer. See https://github.com/pallets/flask/issues/3310
        fix_csrf_session()
        return render_template('home.html', form=CompanySearchForm())

    return redirect(url_for('root.home'))


@authBlueprint.route('/iframe')
def iframe():
    return render_template("auth/iframe.html") if current_user.is_authenticated else ""


@authBlueprint.route('/login/pe-connect-recruiter')
def peam_recruiter_connect():
    # Register siret in session for later
    siret = request.args.get('siret', '')
    if siret:
        session['SIRET'] = siret

    # Register origin in session for later
    origin = request.args.get('origin', '')
    if origin:
        session['ORIGIN'] = origin

    # Register action_name in session for later
    action_name = request.args.get('action_name', '')
    if action_name:
        session['ACTION_NAME'] = action_name

    # First step : get user token
    state = random_string()
    nonce = random_string()

    session['STATE'] = state
    session['NONCE'] = nonce

    scope = "application_{} api_peconnect-entreprisev1 openid profile email habilitation".format(settings.PEAM_CLIENT_ID)

    url = settings.PEAM_AUTH_RECRUITER_BASE_URL + "/connexion/oauth2/authorize?" + urlencode({
        'realm': '/employeur',
        'response_type': 'code',
        'client_id': settings.PEAM_CLIENT_ID,
        'scope': scope,
        'redirect_uri': url_for('auth.peam_recruiter_token_callback', _external=True),
        'state': state,
        'nonce': nonce,
    })

    # Redirect user to ESD login page
    return redirect(url)


@authBlueprint.route('/login/pe-connect-recruiter/callback')
def peam_recruiter_token_callback():
    siret = session.pop('SIRET', '')
    recruiter_from_lba = session.pop('ORIGIN', '') == 'labonnealternance'
    action_name = session.pop('ACTION_NAME', '')

    # State value
    state = request.args.get('state', '')
    session_state = session.get('STATE', '')
    session_nonce = session.get('NONCE', '')

    # Redirect params
    redirect_params = {}
    if siret:
        # Note: if we set siret=None directly in redirect_params, we will have an extra / at the end of the generated url
        # Which will cause a 404 error
        redirect_params.update({'siret': siret})
    if recruiter_from_lba:
        redirect_params.update({'origin': 'labonnealternance'})
    if action_name:
        redirect_params.update({'action_name': action_name})

    # Code value
    code = request.args.get('code', '')

    try:
        if session_state != state:
            raise PeamRecruiterError('Wrong state value {} - {}'.format(session_state, state))
        elif not code:
            raise PeamRecruiterLoginCancelled()

        token_data = get_token_data(code)

        # Token value
        access_token = token_data.get('access_token', '')
        nonce = token_data.get('nonce', '')
        if session_nonce != nonce or not access_token:
            raise PeamRecruiterError('Wrong session nonce or missing access token')

        # User infos
        recruiter_data = get_recruiter_data(access_token)
    except PeamRecruiterError as e:
        logger.exception(e)
    except PeamRecruiterLoginCancelled as e:
        pass
    else:
        # Profile need to be certified (email and habilitation)
        uid = recruiter_data.get('sub', '')
        habilitation = recruiter_data.get('habilitation', '')
        email_verified = recruiter_data.get('email_verified') == 'true'

        if habilitation != 'recruteurcertifie' and not uid and not email_verified:
            redirect_url = url_for('contact_form.ask_recruiter_pe_connect', **redirect_params)
            message = "Votre compte n'est pas certifié. Veuillez recommencer ou utiliser le formulaire sans connexion"
            flash(message, 'error')
            return redirect(redirect_url)

        # Save profile in session
        session[SessionKeys.EMAIL.value] = recruiter_data.get('email', '')
        session[SessionKeys.EMAIL_VERIFIED.value] = email_verified
        session[SessionKeys.FIRSTNAME.value] = recruiter_data.get('given_name', '').capitalize()
        session[SessionKeys.LASTNAME.value] = recruiter_data.get('family_name', '').capitalize()
        session[SessionKeys.HABILITATION.value] = habilitation
        session[SessionKeys.UID.value] = uid

        redirect_url = url_for('contact_form.change_info', **redirect_params)
        return redirect(redirect_url)

    # Fail
    redirect_url = url_for('contact_form.ask_recruiter_pe_connect', **redirect_params)

    message = "Erreur lors de la connexion. Veuillez réessayer ultérieurement ou utiliser le formulaire sans connexion"
    flash(message, 'error')
    return redirect(redirect_url)
