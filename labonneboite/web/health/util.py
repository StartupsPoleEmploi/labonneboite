import logging
from labonneboite.common.database import db_session
from labonneboite.common.es import Elasticsearch

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

