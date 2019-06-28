
from flask import Blueprint
from flask import make_response

from labonneboite.web.health import util as health_util


healthBlueprint = Blueprint('health', __name__)


@healthBlueprint.route('')
def health_all():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot)
    `yes` if Elastic Search and Database are ok
    """
    return health_response(health_util.is_db_alive() and health_util.is_elasticsearch_alive())


@healthBlueprint.route('/db')
def health_db():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot)
    `yes` if Database is ok
    """
    return health_response(health_util.is_db_alive())


@healthBlueprint.route('/es')
def health_es():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot)
    `yes` if Elastic Search is ok
    """
    return health_response(health_util.is_elasticsearch_alive())


@healthBlueprint.route('/uwsgi')
def health_uwsgi():
    """
    Dummy health check to test if uwsgi is up. If this part of the code is reached,
    it obviously means uwsgi is up, so there is nothing to test.
    """
    return health_response(True)


def health_response(is_healthy):
    return make_response("yes" if is_healthy else "no")
