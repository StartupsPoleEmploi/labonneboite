from flask import Blueprint, make_response

from labonneboite.web.health import util as health_util


healthBlueprint = Blueprint("health", __name__)


@healthBlueprint.route("")
def health_all():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot).
    Returns `yes` if internal dependencies (Elastic Search, Database, Uwsgi) are all ok.
    Does not check external dependencies (IGN) nor Redis.    
    """
    return health_response(
        health_util.is_db_alive() and health_util.is_elasticsearch_alive() and health_util.is_uwsgi_alive()
    )


@healthBlueprint.route("/db")
def health_db():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot).
    Returns `yes` if Database is ok.
    """
    return health_response(health_util.is_db_alive())


@healthBlueprint.route("/es")
def health_es():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot).
    Returns `yes` if Elastic Search is ok.
    """
    return health_response(health_util.is_elasticsearch_alive())


@healthBlueprint.route("/redis")
def health_redis():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot).
    Returns `yes` if Redis is ok.
    """
    return health_response(health_util.is_redis_alive())


@healthBlueprint.route("/uwsgi")
def health_uwsgi():
    """
    Health check to test if uwsgi is up.
    """
    return health_response(health_util.is_uwsgi_alive())


@healthBlueprint.route("/ign/duration")
def health_ign_duration():
    """
    Health check to test if IGN API duration is up.
    """
    return health_response(health_util.is_ign_duration_alive())


@healthBlueprint.route("/ign/isochrone")
def health_ign_isochrone():
    """
    Health check to test if IGN API isochrone is up.
    """
    return health_response(health_util.is_ign_isochrone_alive())


def health_response(is_healthy):
    return make_response("yes" if is_healthy else "no")
