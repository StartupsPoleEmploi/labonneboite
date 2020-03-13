import json
import logging
import socket
from collections import OrderedDict
from datetime import datetime

from flask import has_request_context, request
from flask_login import current_user

from labonneboite.conf import settings


# Produce json-formatter logs about user activity. This can be used for debugging
# and analytics, but stats are mostly used to be dumped in the Pôle Emploi data
# lake. Thus, in production activity logs must be dumped to files that will be
# transfered to the data lake.
# Because fields are parsed by the data lake teams, we MUST NOT modify them
# without telling them about it.

logger = logging.getLogger("useractivity")
logger.setLevel(settings.LOG_LEVEL_USER_ACTIVITY)
settings.LOGGING_HANDLER_USER_ACTIVITY.setFormatter(logging.Formatter(settings.LOG_FORMAT_USER_ACTIVITY))
logger.addHandler(settings.LOGGING_HANDLER_USER_ACTIVITY)


def log(event_name, user=None, source=None, **properties):
    if not user and current_user and not current_user.is_anonymous:
        user = current_user
    source = source or "site"

    data = OrderedDict()
    data["dateheure"] = datetime.isoformat(datetime.now())
    data["nom"] = event_name
    data["source"] = source
    data["hote"] = socket.gethostname()
    data["idutilisateur"] = user.id if user else None
    data["idutilisateur-peconnect"] = user.external_id if user else None
    data["url"] = request.full_path if has_request_context() else None
    data["proprietes"] = properties
    logger.info(json.dumps(data))


def log_search(sirets=None, count=None, page=None, source=None, **properties):
    resultats = {"page": page, "total": count, "sirets": sirets}
    log("recherche", source=source, resultats=resultats, **properties)
