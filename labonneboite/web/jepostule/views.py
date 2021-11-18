import logging
from urllib.parse import urlencode

import requests
from flask import abort, Blueprint, flash, jsonify, redirect, render_template, request, Request, url_for
from flask_login import current_user
from werkzeug.exceptions import BadRequest, NotAcceptable

from labonneboite.common import crypto
from labonneboite.common.models.auth import User
from labonneboite.common.models.office import Office
from labonneboite.common.refresh_peam_token import refresh_peam_token
from labonneboite.conf import settings
from labonneboite.services.pole_emploi_io import CoordonneesGetter

from .utils import jepostule_enabled

logger = logging.getLogger('main')
jepostuleBlueprint = Blueprint('jepostule', __name__)


def _get_office_data(current_user: User, office: Office, request: Request):
    data = {
        'candidate_first_name': current_user.first_name,
        'candidate_last_name': current_user.last_name,
        'candidate_email': current_user.email.lower(),
        'candidate_peid': current_user.external_id,
        'candidate_rome_code': request.args.get('rome_code', ''),
        'employer_email': office.email.lower(),
        'employer_description': office.name,
        'siret': office.siret,
        'client_id': settings.JEPOSTULE_CLIENT_ID,
        'next_url': request.referrer or '',
    }

    if settings.FORWARD_PEAM_TOKEN_TO_JP_FOR_AMI:
        candidate_peam_access_token = current_user.get_peam_access_token()
        if candidate_peam_access_token:
            encrypted_candidate_peam_access_token = crypto.encrypt(candidate_peam_access_token)
            data['candidate_peam_access_token'] = encrypted_candidate_peam_access_token

    return data


@refresh_peam_token
@jepostuleBlueprint.route('/candidater/<siret>')
def application(siret):
    office = Office.query.filter_by(siret=siret).first()
    if not jepostule_enabled(current_user, office):
        abort(404)

    data = _get_office_data(
        current_user,
        office,
        request,
    )

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
        response = requests.post(settings.JEPOSTULE_BASE_URL + '/auth/application/token/', data=params, timeout=20)
    except requests.ReadTimeout:
        raise JePostuleError('Request token timeout')

    if response.status_code >= 400:
        raise JePostuleError(
            'Request token error status={response.status_code} content="{response.content}"'.format(response=response)
        )

    try:
        data = response.json()
    except ValueError:
        raise JePostuleError('Request token JSON parsing error content="{response.content}"'.format(response=response))

    return data['token'], data['timestamp']


@jepostuleBlueprint.route('/auto-apply.json', methods=['POST'])
def autoApply():
    """
    Auto apply to a list of office for a job

    POST [application/json]: {
        job: str,
        sirets: str[]
    }
    """
    # TODO: [POC] call jepostule to process the applies
    try:
        sirets = request.json['sirets']
        job = request.json['job']
    except AttributeError as e:
        return jsonify({"message": 'invalid content type, expected application/json'}), NotAcceptable.code
    except TypeError as e:
        return jsonify({"message": 'invalid format, expected a json with sirets and job'}), BadRequest.code
    except KeyError as e:
        return jsonify({"message": 'missing mandatory field : sirets and/or job'}), BadRequest.code
    if (not isinstance(sirets, list)):
        return jsonify({"sirets": 'invalid data type: expected list'}), BadRequest.code
    validations = [*map(lambda siret: None if isinstance(siret, str) else 'invalid data type: expected string', sirets)]
    if any(validations):
        return jsonify({"sirets": validations}), BadRequest.code

    offices = Office.query.filter(Office.siret.in_(sirets)).all()
    access_token = current_user.get_peam_access_token()
    try:
        coordonnees = CoordonneesGetter(access_token).fetch()
        candidate_address = coordonnees.get('fullAddress', '-')
    except:
        candidate_address = '-'

    succeed = []

    for office in offices:
        if office.email:
            data = _get_office_data(
                current_user,
                office,
                request,
            )
            token, timestamp = get_token(**data)
            data['token'] = token
            data['timestamp'] = timestamp
            response = requests.post(
                f"{settings.JEPOSTULE_BASE_URL}/embed/candidater/",
                data=dict(
                    **data,
                    job=job,
                    candidate_address=candidate_address,
                    candidate_phone="-",
                    message="""Bonjour,

    Votre entreprise suscite tout mon intérêt ; c'est pourquoi je me permets aujourd'hui de vous transmettre ma candidature spontanée.

    C'est avec plaisir que je vous rencontrerai lors d'un entretien afin de vous présenter de vive voix mes motivations à rejoindre votre équipe.

    Dans l'attente de votre retour, je reste à votre écoute pour tout complément d'information.""",
                )
            )
            succeed.append(response.status_code < 400)

    if any(succeed):
        return "", 204
    else:
        return jsonify({"message": 'Aucune candidature n\'a été envoyé'}), BadRequest.code


class JePostuleError(Exception):
    pass
