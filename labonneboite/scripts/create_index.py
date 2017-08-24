# coding: utf8
import argparse
import logging

from elasticsearch import Elasticsearch
from elasticsearch import TransportError
from elasticsearch.helpers import bulk
from sqlalchemy import inspect

from labonneboite.common import encoding as encoding_util
from labonneboite.common import geocoding
from labonneboite.common import pdf as pdf_util
from labonneboite.common.database import db_session
from labonneboite.common.load_data import load_ogr_labels, load_ogr_rome_codes
from labonneboite.common.models import Office
from labonneboite.common.models import OfficeAdminAdd, OfficeAdminUpdate, OfficeAdminRemove
from labonneboite.conf import settings
from labonneboite.common import scoring as scoring_util
from labonneboite.common import mapping as mapping_util


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


INDEX_NAME = 'labonneboite'
OFFICE_TYPE = 'office'
ES_TIMEOUT = 30
SCORE_FOR_ROME_MINIMUM = 20  # at least 1.0 stars over 5.0


class StatTracker:
    def __init__(self):
        self.office_count = 0
        self.indexed_office_count = 0
        self.office_score_for_rome_count = 0
    def increment_office_count(self):
        self.office_count += 1
    def increment_indexed_office_count(self):
        self.indexed_office_count += 1
    def increment_office_score_for_rome_count(self):
        self.office_score_for_rome_count += 1

st = StatTracker()


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
        "population": {
            "type": "integer",
        },
        "zipcode": {
            "type": "string",
            "index": "not_analyzed",
        },
        "coordinates": {
            "type": "geo_point",
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
        "headcount": {
            "type": "integer",
            "index": "not_analyzed",
        },
        "location": {
            "type": "geo_point",
        },
    },
}

request_body = {
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

def add_scores_to_request_body():
    for rome_code in settings.ROME_DESCRIPTIONS.keys():
        request_body["mappings"]["office"]["properties"]["score_for_rome_%s" % rome_code] = {
            "type": "integer",
            "index": "not_analyzed"    
        }


add_scores_to_request_body()


def drop_and_create_index(index=INDEX_NAME):
    logging.info("drop and create index...")
    es = Elasticsearch(timeout=ES_TIMEOUT)
    es.indices.delete(index=index, ignore=[400, 404])
    es.indices.create(index=index, body=request_body)


def create_job_codes(index=INDEX_NAME):
    """
    Create the `ogr` type in ElasticSearch.
    """
    logging.info("create job codes...")
    key = 1
    # libelles des appelations pour les codes ROME
    ogr_labels = load_ogr_labels()
    # correspondance appellation vers rome
    ogr_rome_codes = load_ogr_rome_codes()
    es = Elasticsearch(timeout=ES_TIMEOUT)

    for ogr, description in ogr_labels.iteritems():
        rome_code = ogr_rome_codes[ogr]
        try:
            rome_description = settings.ROME_DESCRIPTIONS[rome_code]
        except KeyError:
            rome_description = ""
            logging.info("can't find description for rome %s", rome_code)
            continue
        doc = {
            'ogr_code': ogr,
            'ogr_description': description,
            'rome_code': rome_code,
            'rome_description': rome_description
        }
        es.index(index=index, doc_type='ogr', id=key, body=doc)
        key += 1


def create_locations(index=INDEX_NAME):
    """
    Create the `location` type in ElasticSearch.
    """
    all_cities = geocoding.load_coordinates_for_cities()
    es = Elasticsearch(timeout=ES_TIMEOUT)
    actions = []

    for _, city_name, zipcode, population, latitude, longitude in all_cities:
        try:
            int(city_name)
            continue
        except ValueError:
            # city_name should not be an integer, so we SHOULD go into exception here
            pass

        doc = {
            'zipcode': zipcode,
            'city_name': city_name,
            'location': {'lat': latitude, 'lon': longitude},
            'population': population,
        }

        action = {
            '_op_type': 'index',
            '_index': index,
            '_type': 'location',
            '_source': doc
        }
        actions.append(action)
    bulk(es, actions)


def get_office_as_es_doc(office):
    """
    Return the office as a JSON document suitable for indexation in ElasticSearch.
    The `office` parameter can be an `Office` or an `OfficeAdminAdd` instance.
    """
    # The `headcount` field of an `OfficeAdminAdd` instance has a `code` attribute.
    if hasattr(office.headcount, 'code'):
        headcount = office.headcount.code
    else:
        headcount = office.headcount

    try:
        headcount = int(headcount)
    except ValueError:
        headcount = 0

    # Cleanup exotic characters.
    sanitized_name = encoding_util.sanitize_string(office.office_name)
    sanitized_email = encoding_util.sanitize_string(office.email)
    sanitized_website = encoding_util.sanitize_string(office.website)

    doc = {
        'naf': office.naf,
        'siret': office.siret,
        'score': office.score,
        'headcount': headcount,
        'name': sanitized_name,
        'email': sanitized_email,
        'tel': office.tel,
        'website': sanitized_website,
        'flag_alternance': int(office.flag_alternance),
        'flag_junior': int(office.flag_junior),
        'flag_senior': int(office.flag_senior),
        'flag_handicap': int(office.flag_handicap),
    }

    if office.y and office.x:
        doc['location'] = {
            'lat': office.y,
            'lon': office.x,
        }

    doc = inject_office_rome_scores_into_es_doc(office, doc)

    return doc


def inject_office_rome_scores_into_es_doc(office, doc):
    # fetch all rome_codes mapped to the naf of this office
    # as we will compute a score adjusted for each of them
    try:
        rome_codes = mapping_util.MANUAL_NAF_ROME_MAPPING[office.naf].keys()
    except KeyError:
        # unfortunately some NAF codes have no matching ROME at all
        rome_codes = []

    for rome_code in rome_codes:
        office_score_for_current_rome = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
            score=office.score,
            rome_code=rome_code,
            naf_code=office.naf
        )
        if office_score_for_current_rome >= SCORE_FOR_ROME_MINIMUM:
            st.increment_office_score_for_rome_count()
            doc['score_for_rome_%s' % rome_code] = office_score_for_current_rome

    return doc


def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def create_offices(index=INDEX_NAME, ignore_unreachable_offices=False):
    """
    Create the `office` type in ElasticSearch.
    """
    es = Elasticsearch(timeout=300)

    actions = []

    logging.info("creating offices...")

    for _, office in enumerate(db_session.query(Office).all()):

        st.increment_office_count()
        if st.office_count % 10000 == 0:
            logging.info("already processed %s offices, %s were actually indexed...",
                st.office_count,
                st.indexed_office_count,
                )

        es_doc = get_office_as_es_doc(office)

        office_is_reachable = any(key.startswith('score_for_rome_') for key in es_doc)

        if office_is_reachable or not ignore_unreachable_offices:
            st.increment_indexed_office_count()
            actions.append({
                '_op_type': 'index',
                '_index': index,
                '_type': OFFICE_TYPE,
                '_id': office.siret,
                '_source': es_doc,
            })

    logging.info("chunking index actions")
    batch_actions = chunks(actions, 10000)
    logging.info("chunking done...")
    chunk = 0
    for batch_action in batch_actions:
        logging.info("chunk %s", chunk)
        chunk += 1
        bulk(es, batch_action)


def add_offices(index=INDEX_NAME):
    """
    Add offices (complete the data provided by the importer).
    """
    es = Elasticsearch(timeout=ES_TIMEOUT)

    for office_to_add in db_session.query(OfficeAdminAdd).all():

        office = Office.query.filter_by(siret=office_to_add.siret).first()

        # Only create a new office if it does not already exist.
        # This guarantees that the importer data will always have precedence.
        if not office:

            # The `headcount` field of an `OfficeAdminAdd` instance has a `code` attribute.
            if hasattr(office_to_add.headcount, 'code'):
                headcount = office_to_add.headcount.code
            else:
                headcount = office_to_add.headcount

            # Create the new office in DB.
            new_office = Office()
            # Use `inspect` because `Office` columns are named distinctly from attributes.
            for field_name in inspect(Office).columns.keys():
                value = getattr(office_to_add, field_name)
                if field_name == 'headcount':
                    value = headcount
                setattr(new_office, field_name, value)
            db_session.add(new_office)
            db_session.commit()

            # Create the new office in ES.
            doc = get_office_as_es_doc(office_to_add)
            es.create(index=index, doc_type=OFFICE_TYPE, id=office_to_add.siret, body=doc)


def remove_offices(index=INDEX_NAME):
    """
    Remove offices (overload the data provided by the importer).
    """
    es = Elasticsearch(timeout=ES_TIMEOUT)

    # When returning multiple rows, the SQLAlchemy Query class can only give them out as tuples.
    # We need to unpack them explicitly.
    offices_to_remove = [siret for (siret,) in db_session.query(OfficeAdminRemove.siret).all()]

    for siret in offices_to_remove:
        # Apply changes in ElasticSearch.
        try:
            es.delete(index=index, doc_type=OFFICE_TYPE, id=siret)
        except TransportError as e:
            if e.status_code != 404:
                raise
        # Apply changes in DB.
        office = Office.query.filter_by(siret=siret).first()
        if office:
            office.delete()
            # Delete the current PDF.
            pdf_util.delete_file(office)


def update_offices(index=INDEX_NAME):
    """
    Update offices (overload the data provided by the importer).
    """
    es = Elasticsearch(timeout=ES_TIMEOUT)

    for office_to_update in db_session.query(OfficeAdminUpdate).all():

        office = Office.query.filter_by(siret=office_to_update.siret).first()

        if office:

            # Apply changes in DB.
            office.email = u'' if office_to_update.remove_email else (office_to_update.new_email or office.email)
            office.tel = u'' if office_to_update.remove_phone else (office_to_update.new_phone or office.tel)
            office.website = u'' if office_to_update.remove_website else (
                office_to_update.new_website or office.website)
            if office_to_update.new_score:
                office.score = office_to_update.new_score
            office.save()

            # Apply changes in ElasticSearch.
            body = {'doc': {'email': office.email, 'phone': office.tel, 'website': office.website}}
            if office_to_update.new_score:
                body['doc']['score'] = office_to_update.new_score
                body['doc'] = inject_office_rome_scores_into_es_doc(office, body['doc'])
            es.update(index=index, doc_type=OFFICE_TYPE, id=office_to_update.siret, body=body, ignore=404)

            # Delete the current PDF, it will be regenerated at next download attempt.
            pdf_util.delete_file(office)


def display_performance_stats():
    methods = [
               'get_score_from_hirings',
               'get_hirings_from_score',
               'get_score_adjusted_to_rome_code_and_naf_code',
              ]
    for method in methods:
        logging.info("%s : %s", method, getattr(scoring_util, method).cache_info())

    logging.info("indexed %s of %s offices and %s score_for_rome",
        st.indexed_office_count,
        st.office_count,
        st.office_score_for_rome_count
        )


def run():
    parser = argparse.ArgumentParser(description="Update etablissement data with geographic coordinates")
    parser.add_argument('-d', '--drop-indexes', dest='drop_indexes', help="Drop indexs before updating documents")
    args = parser.parse_args()

    if args.drop_indexes:
        logging.info("drop index")
        drop_and_create_index()
        create_offices(ignore_unreachable_offices=True)
        create_job_codes()
        create_locations()

    # Upon requests received from employers we can add, remove or update offices.
    # This permits us to complete or overload the data provided by the importer.
    add_offices()
    remove_offices()
    update_offices()

    display_performance_stats()


if __name__ == '__main__':
    run()
