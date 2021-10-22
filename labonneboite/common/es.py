from datetime import datetime
import random
import string

import elasticsearch

from labonneboite.conf import settings

OFFICE_TYPE = 'office'
OGR_TYPE = 'ogr'
LOCATION_TYPE = 'location'


class ConnectionPool(object):
    ELASTICSEARCH_INSTANCE = None


def Elasticsearch():
    """
    Elasticsearch client singleton. All connections to ES should go through
    this client, so that we can reuse ES connections and not flood ES with new
    connections.
    """
    if not ConnectionPool.ELASTICSEARCH_INSTANCE:
        ConnectionPool.ELASTICSEARCH_INSTANCE = new_elasticsearch_instance()
    return ConnectionPool.ELASTICSEARCH_INSTANCE


def new_elasticsearch_instance():
    """
    In some cases e.g. parallel jobs you may need a dedicated es connection for each
    of your threads.
    """
    return elasticsearch.Elasticsearch(
        hosts=[settings.ES_HOST],
        timeout=settings.ES_TIMEOUT
    )


def drop_and_create_index():
    """
    Delete all indexes associated to reference alias and create a new index
    that points to the alias.

    WARNING: this will create downtime for Elasticsearch. You should probably
    not use this function to recreate the ES database in production.
    """
    drop_indexes_of_alias()

    new_index_name = get_new_index_name()
    create_index(new_index_name)
    add_alias_to_index(new_index_name)


def drop_indexes_of_alias(name=settings.ES_INDEX):
    """
    Drop indexes associated to alias.
    """
    for index in list(Elasticsearch().indices.get_alias(name).keys()):
        drop_index(index=index)


def drop_index(index):
    Elasticsearch().indices.delete(index=index, params={'ignore': [400, 404]})


def get_new_index_name():
    """
    Create an index name based on the current date and time. A random string is
    appended to avoid collisions for indexes created at the same second (it
    happens in tests).
    """
    suffix = ''.join([random.choice(string.ascii_lowercase) for _ in range(5)])
    return datetime.now().strftime(settings.ES_INDEX + "-%Y%m%d%H%M%S-" + suffix)


def add_alias_to_index(index, name=settings.ES_INDEX):
    Elasticsearch().indices.put_alias(index=index, name=name)


def create_index(index):
    """
    Create index with the right settings.
    """
    filters = {
        "stop_francais": {
            "type": "stop",
            "stopwords": ["_french_"],
        },
        "fr_stemmer": {
            "type": "stemmer",
            "name": "light_french",
        },
        "elision": {
            "type": "elision",
            "articles": ["c", "l", "m", "t", "qu", "n", "s", "j", "d"],
        },
        "ngram_filter": {
            "type": "ngram",
            "min_gram": 2,
            "max_gram": 3,
        },
        "edge_ngram_filter": {
            "type": "edge_ngram",
            "min_gram": 1,
            "max_gram": 2,
        },
    }

    analyzers = {
        "stemmed": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "asciifolding",
                "lowercase",
                "stop_francais",
                "elision",
                "fr_stemmer",
            ],
        },
        "autocomplete": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "lowercase",
                "edge_ngram_filter",
            ],
        },
        "ngram_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "asciifolding",
                "lowercase",
                "stop_francais",
                "elision",
                "ngram_filter",
            ],
        },
    }

    mapping_ogr = {
        # https://www.elastic.co/guide/en/elasticsearch/reference/1.7/mapping-all-field.html
        # "_all": {
        #     "type": "text",
        #     "analyzer": "ngram_analyzer",
        #     "search_analyzer": "standard",
        # },
        "properties": {
            "ogr_code": {
                "type": "text",
            },
            "ogr_description": {
                "type": "text",
                "term_vector": "yes",
                "analyzer": "ngram_analyzer",
                "search_analyzer": "standard",
            },
            "rome_code": {
                "type": "text",
            },
            "rome_description": {
                "type": "text",
                "term_vector": "yes",
                "analyzer": "ngram_analyzer",
                "search_analyzer": "standard",
            },
        },
    }

    mapping_location = {
        "properties": {
            "city_name": {
                "type": "text",
                "fields": {
                    "raw": {
                        "type": "text",
                    },
                    "autocomplete" : {
                        "type": "text",
                        "analyzer": "autocomplete",
                    },
                    "stemmed": {
                        "type": "text",
                        "analyzer": "stemmed",
                        "store": "true",
                        "term_vector": "yes",
                    },
                },
            },
            "coordinates": {
                "type": "geo_point",
            },
            "population": {
                "type": "integer",
            },
            "slug": {
                "type": "text",
            },
            "zipcode": {
                "type": "text",
            },
        },
    }

    mapping_office = {
        "properties": {
            "naf": {
                "type": "text",
            },
            "siret": {
                "type": "text",
            },
            "name": {
                "type": "text",
            },
            "email": {
                "type": "text",
            },
            "tel": {
                "type": "text",
            },
            "website": {
                "type": "text",
            },
            "score": {
                "type": "integer",
            },
            "scores_by_rome": {
                "type": "object",
            },
            "score_alternance": {
                "type": "integer",
            },
            "scores_alternance_by_rome": {
                "type": "object",
            },
            "boosted_romes": {
                "type": "object",
            },
            "boosted_alternance_romes": {
                "type": "object",
            },
            "headcount": {
                "type": "integer",
            },
            "department": {
                "type": "text",
            },
            "locations": {
                "type": "geo_point",
            },
        },
    }
    create_body = {
        "settings": {
            "index": {
                "analysis": {
                    "filter": filters,
                    "analyzer": analyzers,
                },
            },
        },
        "mappings":  {
            "properties": {
                "ogr": mapping_ogr,
                "location": mapping_location,
                "office": mapping_office,
            },
        },
    }

    Elasticsearch().indices.create(index=index, body=create_body)

    # fake_doc = fake_office()
    # Elasticsearch().index(index=index, doc_type=OFFICE_TYPE, id=fake_doc['siret'], body=fake_doc)

# This fake office having a zero but existing score for each rome is designed
# as a workaround of the following bug:
#
# ElasticsearchException[Unable to find a field mapper for field [scores_by_rome.A0000]]
# which happens when a rome is orphaned (no company has a score for this rome).
#
# The following ES bug is known and has been fixed in ES 2.1.0
# https://github.com/elastic/elasticsearch/pull/13060
# however as of Jan 2018 we are using Elasticsearch 1.7 so we have to live with it.
#
# When the field_value_factor clause is applied to a non existing field (this is
# the case for an orphaned rome i.e. no company has a score_for_rome.A0000 field for it),
# even if the field_value_factor clause has a 'missing' value, the ES request will still fail
# with a 'Unable to find a field mapper for field' error. This is fixed in ES 2.1.0.
#
# When this happens in a single rome search, the bug can silently be ignored as this means
# the search result will be empty anyway, but this is no longer possible with a multi rome search.
#
# This fake office ensures no rome will ever be orphaned.
# def fake_office():
#     doc = {
#         'siret': "0",
#         # fields required even if not used by function_score
#         'score': 0,
#         'score_alternance': 0,
#     }
# 
#     # all fields used by function_score which could potentially be orphaned and thus cause the bug
#     doc['scores_by_rome'] = {rome: 0 for rome in settings.ROME_DESCRIPTIONS}
#     doc['scores_alternance_by_rome'] = {rome: 0 for rome in settings.ROME_DESCRIPTIONS}
# 
#     return doc
