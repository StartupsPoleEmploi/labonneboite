import logging
from urllib.parse import urlencode

from flask import abort, Blueprint, render_template, request, redirect
from flask_login import current_user
import requests

from labonneboite.conf import settings
from labonneboite.common import crypto
from labonneboite.common.models.office import Office
from labonneboite.common.refresh_peam_token import attempt_to_refresh_peam_token

from .utils import jepostule_enabled

logger = logging.getLogger('main')
jepostuleBlueprint = Blueprint('jepostule', __name__)


@jepostuleBlueprint.route('/candidater/<siret>')
def application(siret):
    company = Office.query.filter_by(siret=siret).first()
    if not jepostule_enabled(current_user, company):
        abort(404)

    refresh_token_result = attempt_to_refresh_peam_token()
    if refresh_token_result["token_has_expired"]:
        return redirect(refresh_token_result["redirect_url"])

    data = {
        'candidate_first_name': current_user.first_name,
        'candidate_last_name': current_user.last_name,
        'candidate_email': current_user.email.lower(),
        'candidate_peid': current_user.external_id,
        'candidate_rome_code': request.args.get('rome_code', ''),
        'employer_email': company.email.lower(),
        'employer_description': company.name,
        'siret': siret,
        'client_id': settings.JEPOSTULE_CLIENT_ID,
        'next_url': request.referrer or '',
    }

    if settings.FORWARD_PEAM_TOKEN_TO_JP_FOR_AMI:
        candidate_peam_access_token = current_user.get_peam_access_token()
        if candidate_peam_access_token:
            encrypted_candidate_peam_access_token = crypto.encrypt(candidate_peam_access_token)
            data['candidate_peam_access_token'] = encrypted_candidate_peam_access_token

    token, timestamp = get_token(**data)
    data['token'] = token
    data['timestamp'] = timestamp
    return render_template(
        'jepostule/candidater.html',
        iframe_path="/embed/candidater/?" + urlencode(data),
        iframe_base=settings.JEPOSTULE_BASE_URL,
    )


def get_token(**params):
    params['client_secret'] = settings.JEPOSTULE_CLIENT_SECRET
    try:
        response = requests.post(
            settings.JEPOSTULE_BASE_URL + '/auth/application/token/',
            data=params, timeout=20
        )
    except requests.ReadTimeout:
        raise JePostuleError('Request token timeout')

    if response.status_code >= 400:
        raise JePostuleError('Request token error status={response.status_code} content="{response.content}"'.format(
            response=response
        ))

    try:
        data = response.json()
    except ValueError:
        raise JePostuleError('Request token JSON parsing error content="{response.content}"'.format(
            response=response
        ))

    return data['token'], data['timestamp']


class JePostuleError(Exception):
    pass
