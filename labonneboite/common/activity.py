from collections import OrderedDict
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import json
import logging
import socket
import uuid

from flask import has_request_context, request
from flask_login import current_user

from labonneboite.conf import settings

# Produce json-formatter logs about user activity. This can be used for debugging
# and analytics, but stats are mostly used to be dumped in the Pôle Emploi data
# lake. Thus, in production activity logs must be dumped to files that will be
# transfered to the data lake.
# Because fields are parsed by the data lake teams, we MUST NOT modify them
# without telling them about it.

userLogger = logging.getLogger('useractivity')
userLogger.setLevel(settings.LOG_LEVEL_USER_ACTIVITY)
settings.LOGGING_HANDLER_USER_ACTIVITY.setFormatter(logging.Formatter(settings.LOG_FORMAT_USER_ACTIVITY))
userLogger.addHandler(settings.LOGGING_HANDLER_USER_ACTIVITY)


def log(event_name, user=None, source=None, **properties):
    if not user and current_user and not current_user.is_anonymous:
        user = current_user

    if has_request_context():
        # When we log in the context of an ajax call, e.g. 'detail entreprise',
        #   the params of the search are not present in the URL,
        # Also the referrer will not have any query params
        # In local dev it has but not in production, because of a header and security
        # So we expect ajax calls to send params explicitely
        dic = request.values.to_dict()
        args = dict((k.lower(), v) for k, v in dic.items()) # all keys to lowercase as this will be stored as JSON
        args.pop('csrf_token', None) # Keep this out of the logs
    else:
        args = None

    source = source or 'site'

    data = OrderedDict()
    data['dateheure'] = datetime.isoformat(datetime.now())
    data['nom'] = event_name
    data['source'] = source
    data['hote'] = socket.gethostname()
    data['idutilisateur'] = user.id if user else None
    data['idutilisateur-peconnect'] = user.external_id if user else None
    data['url'] = request.full_path if has_request_context() else None
    data['args'] = args
    data['proprietes'] = properties
    userLogger.info(json.dumps(data))

def log_search(sirets=None, count=None, page=None, source=None, **properties):
    resultats = {
        'page': page,
        'total': count,
        'sirets': sirets,
    }
    log('recherche', source=source, resultats=resultats, **properties)

apiLogger = logging.getLogger('apiactivity')
apiLogger.setLevel(settings.LOG_LEVEL_USER_ACTIVITY)
settings.LOGGING_HANDLER_API_ACTIVITY.setFormatter(logging.Formatter(settings.LOG_FORMAT_USER_ACTIVITY))
apiLogger.addHandler(settings.LOGGING_HANDLER_API_ACTIVITY)

def log_api(status, application, user_agent, referrer, remote_addr):
    data = OrderedDict()

    data['startup'] = settings.LOG_API_ID
    data['requestId'] = str(uuid.uuid1())
    data['date'] = datetime.isoformat(datetime.now())
    data['remoteIP'] = remote_addr
    data['httpReferer'] = referrer
    data['httpUserAgent'] = user_agent
    data['application'] = application
    data['apiVersion'] = '1'
    data['status'] = status
    # TODO: data['widget'] = False

    apiLogger.info(json.dumps(data))
