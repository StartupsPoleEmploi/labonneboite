from elasticsearch import Elasticsearch
from labonneboite.common.database import db_session  # This is how we talk to the database.


def is_db_alive():
    try:
        db_session.execute('SELECT NOW()').first()
        return True
    except:
        return False


def is_elasticsearch_alive():
    try:
        es = Elasticsearch()
        es.ping()
        return True
    except:
        return False
