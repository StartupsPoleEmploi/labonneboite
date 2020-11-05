import logging
from labonneboite.common.database import db_session
from labonneboite.common.es import Elasticsearch
from labonneboite.common.maps.vendors import ign

logger = logging.getLogger('main')


def is_db_alive():
    try:
        db_session.execute('SELECT NOW()').first()
        return True
    # pylint: disable=W0703
    except Exception as e:
        logger.exception(e)
        return False


def is_elasticsearch_alive():
    try:
        es = Elasticsearch()
        es.ping()
        return True
    # pylint: disable=W0703
    except Exception as e:
        logger.exception(e)
        return False


def is_uwsgi_alive():
    """
    If this part of the code is reached,
    it obviously means uwsgi is up, so there is nothing to test.
    """
    return True


def is_ign_duration_alive():
    endpoint = 'itineraire/rest/route.json'
    params = {
        'destination': '6.1697400,49.1080000',
        'graphName': 'Voiture',
        'origin': '6.1760260,49.1191460',
    }

    try:
        return ign.request_json_api(endpoint, params, timeout=ign.REQUEST_TIMEOUT_SECONDS)["status"] == 'OK'
    # pylint: disable=W0703
    except Exception as e:
        logger.exception(e)
        return False


def is_ign_isochrone_alive():
    endpoint = 'isochrone/isochrone.json'
    params = {
        'location': '4.2645464,48.5300431',
        'smoothing': 'true',
        'time': 1800,
    }

    try:
        return ign.request_json_api(endpoint, params, timeout=ign.REQUEST_TIMEOUT_SECONDS)["status"] == 'OK'
    # pylint: disable=W0703
    except Exception as e:
        logger.exception(e)
        return False
