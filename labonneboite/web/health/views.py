# coding: utf8

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
    if health_util.is_db_alive() and health_util.is_elasticsearch_alive():
        return make_response("yes")
    else:
        return make_response("no")


@healthBlueprint.route('/db')
def health_db():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot)
    `yes` if Database is ok
    """
    if health_util.is_db_alive():
        return make_response("yes")
    else:
        return make_response("no")

@healthBlueprint.route('/es')
def health_es():
    """
    Health check route designed to be regularly monitored in production (e.g. UptimeRobot)
    `yes` if Elastic Search is ok
    """
    if health_util.is_elasticsearch_alive():
        return make_response("yes")
    else:
        return make_response("no")
