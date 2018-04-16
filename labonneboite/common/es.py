from datetime import datetime
import random
import string

import elasticsearch

from labonneboite.conf import settings


class ConnectionPool(object):
    ELASTICSEARCH_INSTANCE = None


def Elasticsearch():
    """
    Elasticsearch client singleton. All connections to ES should go through
    this client, so that we can reuse ES connections and not flood ES with new
    connections.
    """
    if ConnectionPool.ELASTICSEARCH_INSTANCE is None:
        ConnectionPool.ELASTICSEARCH_INSTANCE = elasticsearch.Elasticsearch()
    return ConnectionPool.ELASTICSEARCH_INSTANCE


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
    es = Elasticsearch()
    for index in es.indices.get_alias(name).keys():
        drop_index(index=index)


def drop_index(index):
    es = Elasticsearch()
    es.indices.delete(index=index, params={'ignore': [400, 404]})


def get_new_index_name():
    """
    Create an index name based on the current date and time. A random string is
    appended to avoid collisions for indexes created at the same second (it
    happens in tests).
    """
    suffix = ''.join([random.choice(string.ascii_lowercase) for _ in range(5)])
    return datetime.now().strftime(settings.ES_INDEX + "-%Y%m%d%H%M%S-" + suffix)


def add_alias_to_index(index, name=settings.ES_INDEX):
    es = Elasticsearch()
    es.indices.put_alias(index=index, name=name)


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
            "max_gram": 20,
        },
        "edge_ngram_filter": {
            "type": "edge_ngram",
            "min_gram": 1,
            "max_gram": 20,
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
        "_all": {
            "type": "string",
            "index_analyzer": "ngram_analyzer",
            "search_analyzer": "standard",
        },
        "properties": {
            "ogr_code": {
                "type": "string",
                "index": "not_analyzed",
            },
            "ogr_description": {
                "type": "string",
                "include_in_all": True,
                "term_vector": "yes",
                "index_analyzer": "ngram_analyzer",
                "search_analyzer": "standard",
            },
            "rome_code": {
                "type": "string",
                "index": "not_analyzed",
            },
            "rome_description": {
                "type": "string",
                "include_in_all": True,
                "term_vector": "yes",
                "index_analyzer": "ngram_analyzer",
                "search_analyzer": "standard",
            },
        },
    }

    mapping_location = {
        "properties": {
            "city_name": {
                "type": "multi_field",
                "fields": {
                    "raw": {
                        "type": "string",
                        "index": "not_analyzed",
                    },
                    "autocomplete" : {
                        "type": "string",
                        "analyzer": "autocomplete",
                    },
                    "stemmed": {
                        "type": "string",
                        "analyzer": "stemmed",
                        "store": "yes",
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
                "type": "string",
                "index": "not_analyzed",
            },
            "zipcode": {
                "type": "string",
                "index": "not_analyzed",
            },
        },
    }

    mapping_office = {
        "properties": {
            "naf": {
                "type": "string",
                "index": "not_analyzed",
            },
            "siret": {
                "type": "string",
                "index": "not_analyzed",
            },
            "name": {
                "type": "string",
                "index": "not_analyzed",
            },
            "email": {
                "type": "string",
                "index": "not_analyzed",
            },
            "tel": {
                "type": "string",
                "index": "not_analyzed",
            },
            "website": {
                "type": "string",
                "index": "not_analyzed",
            },
            "score": {
                "type": "integer",
                "index": "not_analyzed",
            },
            "scores_by_rome": {
                "type": "object",
                "index": "not_analyzed",
            },
            "score_alternance": {
                "type": "integer",
                "index": "not_analyzed",
            },
            "scores_alternance_by_rome": {
                "type": "object",
                "index": "not_analyzed",
            },
            "boosted_romes": {
                "type": "object",
                "index": "not_analyzed",
            },
            "headcount": {
                "type": "integer",
                "index": "not_analyzed",
            },
            "department": {
                "type": "string",
                "index": "not_analyzed"
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
            "ogr": mapping_ogr,
            "location": mapping_location,
            "office": mapping_office,
        },
    }

    es = Elasticsearch()
    es.indices.create(index=index, body=create_body)
