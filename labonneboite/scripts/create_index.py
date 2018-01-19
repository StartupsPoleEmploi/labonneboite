# coding: utf8
import argparse
import logging
import os

import multiprocessing as mp
from cProfile import Profile
from pyprof2calltree import convert
from elasticsearch import Elasticsearch
from elasticsearch import TransportError
from elasticsearch.helpers import bulk
from sqlalchemy import inspect

from labonneboite.common import encoding as encoding_util
from labonneboite.common.util import timeit
from labonneboite.common import geocoding
from labonneboite.common import departements as dpt
from labonneboite.common import mapping as mapping_util
from labonneboite.common import pdf as pdf_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common.database import db_session
from labonneboite.common.load_data import load_ogr_labels, load_ogr_rome_mapping
from labonneboite.common.models import Office
from labonneboite.common.models import OfficeAdminAdd, OfficeAdminExtraGeoLocation, OfficeAdminUpdate, OfficeAdminRemove
from labonneboite.conf import settings


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


# FIXME shouldn't create_index script also be used to populate test ES index as well?
# we should use settings.ES_INDEX here instead
INDEX_NAME = 'labonneboite'

OFFICE_TYPE = 'office'
OGR_TYPE = 'ogr'
LOCATION_TYPE = 'location'
ES_TIMEOUT = 300
ES_BULK_CHUNK_SIZE = 10000  # default value is 500
SCORE_FOR_ROME_MINIMUM = 20  # at least 1.0 stars over 5.0


class Counter(object):
    """
    Counter class without the race-condition bug.
    Needed to be able to have a variable (counter) shared between all parallel jobs.
    Inspired from https://stackoverflow.com/questions/2080660/python-multiprocessing-and-a-shared-counter
    """
    def __init__(self):
        self.val = mp.Value('i', 0)

    def increment(self, n=1):
        with self.val.get_lock():
            self.val.value += n

    @property
    def value(self):
        return self.val.value


completed_jobs_counter = Counter()


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


@timeit
def drop_and_create_index():
    logging.info("drop and create index...")
    es = Elasticsearch(timeout=ES_TIMEOUT)
    es.indices.delete(index=INDEX_NAME, params={'ignore': [400, 404]})
    es.indices.create(index=INDEX_NAME, body=request_body)


def bulk_actions(actions):
    es = Elasticsearch(timeout=ES_TIMEOUT)
    # unfortunately parallel_bulk is not available in the current elasticsearch version
    # http://elasticsearch-py.readthedocs.io/en/master/helpers.html
    bulk(es, actions, chunk_size=ES_BULK_CHUNK_SIZE)


@timeit
def create_job_codes():
    """
    Create the `ogr` type in ElasticSearch.
    """
    logging.info("create job codes...")
    # libelles des appelations pour les codes ROME
    ogr_labels = load_ogr_labels()
    # correspondance appellation vers rome
    ogr_rome_codes = load_ogr_rome_mapping()
    actions = []

    for ogr, description in ogr_labels.iteritems():
        if ogr in ogr_rome_codes:
            rome_code = ogr_rome_codes[ogr]
            rome_description = settings.ROME_DESCRIPTIONS[rome_code]
            doc = {
                'ogr_code': ogr,
                'ogr_description': description,
                'rome_code': rome_code,
                'rome_description': rome_description
            }
            action = {
                '_op_type': 'index',
                '_index': INDEX_NAME,
                '_type': OGR_TYPE,
                '_source': doc
            }
            actions.append(action)
    bulk_actions(actions)


@timeit
def create_locations():
    """
    Create the `location` type in ElasticSearch.
    """
    actions = []
    for city in geocoding.get_cities():
        doc = {
            'city_name': city['name'],
            'location': {'lat': city['coords']['lat'], 'lon': city['coords']['lon']},
            'population': city['population'],
            'slug': city['slug'],
            'zipcode': city['zipcode'],
        }
        action = {
            '_op_type': 'index',
            '_index': INDEX_NAME,
            '_type': LOCATION_TYPE,
            '_source': doc
        }
        actions.append(action)

    bulk_actions(actions)


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
        'department': office.departement,
        'flag_alternance': int(office.flag_alternance),
        'flag_junior': int(office.flag_junior),
        'flag_senior': int(office.flag_senior),
        'flag_handicap': int(office.flag_handicap),
    }

    if office.y and office.x:
        # Use an array to allow multiple locations per document, see https://goo.gl/fdTaEM
        # Multiple locations may be added later via the admin UI.
        doc['locations'] = [
            {'lat': office.y, 'lon': office.x},
        ]

    scores_by_rome = get_scores_by_rome(office)
    if scores_by_rome:
        doc['scores_by_rome'] = scores_by_rome

    return doc


def get_scores_by_rome(office, office_to_update=None):
    scores_by_rome = {}

    # fetch all rome_codes mapped to the naf of this office
    # as we will compute a score adjusted for each of them
    office_nafs = [office.naf]
    # Handle NAFs added to a company
    if office_to_update:
        office_nafs += office_to_update.as_list(office_to_update.nafs_to_add)

    romes_to_boost = []
    romes_to_remove = []
    if office_to_update:
        romes_to_boost = office_to_update.as_list(office_to_update.romes_to_boost)
        romes_to_remove = office_to_update.as_list(office_to_update.romes_to_remove)

    for naf in office_nafs:
        try:
            rome_codes = mapping_util.get_romes_for_naf(naf)
        except KeyError:
            # unfortunately some NAF codes have no matching ROME at all
            continue

        # Add unrelated rome for indexing (with boost) and remove unwanted romes
        rome_codes = set(rome_codes).union(set(romes_to_boost)) - set(romes_to_remove)

        for rome_code in rome_codes:
            score = 0

            # With boosting.
            if office_to_update and office_to_update.boost:
                if not office_to_update.romes_to_boost:
                    # Boost the score for all ROME codes.
                    # @vermeer guaranteed that a "real" score will never be equal to 100.
                    score = 100
                else:
                    # Boost the score for some ROME codes only.
                    if rome_code in romes_to_boost:
                        score = 100
                    else:
                        score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                            score=office.score,
                            rome_code=rome_code,
                            naf_code=naf)

            # Without boosting.
            else:
                score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
                    score=office.score,
                    rome_code=rome_code,
                    naf_code=naf)

            if score >= SCORE_FOR_ROME_MINIMUM:
                if rome_code in scores_by_rome and score > scores_by_rome[rome_code]:
                    scores_by_rome[rome_code] = score
                else:
                    scores_by_rome[rome_code] = score
                    st.increment_office_score_for_rome_count()

    return scores_by_rome


def create_offices(enable_profiling=False, disable_parallel_computing=False):
    """
    Populate the `office` type in ElasticSearch.
    Run it as a parallel computation based on departements.
    """
    if enable_profiling:
        func = profile_create_offices_for_departement
    else:
        func = create_offices_for_departement

    if disable_parallel_computing:
        for departement in dpt.DEPARTEMENTS:
            func(departement)
        return

    # Use parallel computing on all available CPU cores.
    # Use even slightly more than avaible CPUs because in practise a job does not always
    # use 100% of a cpu.
    # maxtasksperchild default is infinite, which means memory is never freed up, and grows indefinitely :-/
    # maxtasksperchild=1 ensures memory is freed up after every departement computation.
    pool = mp.Pool(processes=int(1.25*mp.cpu_count()), maxtasksperchild=1)
    pool.map(func, dpt.DEPARTEMENTS_WITH_LARGEST_ONES_FIRST)
    pool.close()
    pool.join()


@timeit
def create_offices_for_departement(departement):
    """
    Populate the `office` type in ElasticSearch with offices having given departement.
    """
    actions = []

    logging.info("STARTED indexing offices for departement=%s ...", departement)

    for _, office in enumerate(db_session.query(Office).filter_by(departement=departement).all()):

        st.increment_office_count()

        es_doc = get_office_as_es_doc(office)

        office_is_reachable = 'scores_by_rome' in es_doc

        if office_is_reachable:
            st.increment_indexed_office_count()
            actions.append({
                '_op_type': 'index',
                '_index': INDEX_NAME,
                '_type': OFFICE_TYPE,
                '_id': office.siret,
                '_source': es_doc,
            })

    bulk_actions(actions)

    completed_jobs_counter.increment()

    logging.info(
        "COMPLETED indexing offices for departement=%s (%s of %s jobs completed)",
        departement,
        completed_jobs_counter.value,
        len(dpt.DEPARTEMENTS),
    )

    display_performance_stats(departement)


def profile_create_offices_for_departement(departement):
    """
    Run create_offices_for_departement with profiling.
    """
    profiler = Profile()
    command = "create_offices_for_departement('%s')" % departement
    profiler.runctx(command, locals(), globals())
    relative_filename = 'profiling_results/create_index_dpt%s.kgrind' % departement
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_filename)
    convert(profiler.getstats(), filename)


@timeit
def add_offices():
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
                try:
                    value = getattr(office_to_add, field_name)
                except AttributeError:
                    # Some fields are not shared between `Office` and `OfficeAdminAdd`.
                    continue
                if field_name == 'headcount':
                    value = headcount
                setattr(new_office, field_name, value)
            db_session.add(new_office)
            db_session.commit()

            # Create the new office in ES.
            doc = get_office_as_es_doc(office_to_add)
            es.create(index=INDEX_NAME, doc_type=OFFICE_TYPE, id=office_to_add.siret, body=doc)


@timeit
def remove_offices():
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
            es.delete(index=INDEX_NAME, doc_type=OFFICE_TYPE, id=siret)
        except TransportError as e:
            if e.status_code != 404:
                raise
        # Apply changes in DB.
        office = Office.query.filter_by(siret=siret).first()
        if office:
            office.delete()
            # Delete the current PDF.
            pdf_util.delete_file(office)


@timeit
def update_offices():
    """
    Update offices (overload the data provided by the importer).
    """
    es = Elasticsearch(timeout=ES_TIMEOUT)

    for office_to_update in db_session.query(OfficeAdminUpdate).all():
        for siret in OfficeAdminUpdate.as_list(office_to_update.sirets):

            office = Office.query.filter_by(siret=siret).first()

            if office:
                # Apply changes in DB.
                office.email = u'' if office_to_update.remove_email else (office_to_update.new_email or office.email)
                office.email_alternance = u'' if office_to_update.remove_flag_alternance else (office_to_update.email_alternance or u'')
                office.tel = u'' if office_to_update.remove_phone else (office_to_update.new_phone or office.tel)
                office.website = u'' if office_to_update.remove_website else (office_to_update.new_website or office.website)
                office.flag_alternance = False if office_to_update.remove_flag_alternance else office.flag_alternance
                office.save()

                # Apply changes in ElasticSearch.
                body = {'doc':
                    {'email': office.email, 'phone': office.tel, 'website': office.website,
                    'flag_alternance': 1 if office.flag_alternance else 0 }
                }

                scores_by_rome = get_scores_by_rome(office, office_to_update)
                if scores_by_rome:
                    body['doc']['scores_by_rome'] = scores_by_rome

                # The update API makes partial updates: existing `scalar` fields are overwritten,
                # but `objects` fields are merged together.
                # https://www.elastic.co/guide/en/elasticsearch/guide/1.x/partial-updates.html
                # However `scores_by_rome` needs to be overwritten because it may change over time.
                # To do this, we perform 2 requests: the first one reset `scores_by_rome`, the
                # second one populate it.
                delete_body = {'doc': {'scores_by_rome': None}}

                # Unfortunately these cannot easily be bulked :-(
                # The reason is there is no way to tell bulk to ignore missing documents (404)
                # for a partial update. Tried it and failed it on Oct 2017 @vermeer.
                es.update(index=INDEX_NAME, doc_type=OFFICE_TYPE, id=siret, body=delete_body,
                        params={'ignore': 404})
                es.update(index=INDEX_NAME, doc_type=OFFICE_TYPE, id=siret, body=body,
                        params={'ignore': 404})

                # Delete the current PDF, it will be regenerated at next download attempt.
                pdf_util.delete_file(office)

@timeit
def update_offices_geolocations():
    """
    Remove or add extra geolocations to offices.
    New geolocations are entered into the system through the `OfficeAdminExtraGeoLocation` table.
    """
    es = Elasticsearch(timeout=ES_TIMEOUT)

    for extra_geolocation in db_session.query(OfficeAdminExtraGeoLocation).all():
        office = Office.query.filter_by(siret=extra_geolocation.siret).first()
        if office:
            locations = []
            if office.y and office.x:
                locations.append({'lat': office.y, 'lon': office.x})
            if not extra_geolocation.is_outdated():
                locations.extend(extra_geolocation.geolocations_as_lat_lon_properties())
                office.has_multi_geolocations = True
            else:
                office.has_multi_geolocations = False
            # Apply changes in DB.
            office.save()
            # Apply changes in ElasticSearch.
            body = {'doc': {'locations': locations}}
            es.update(index=INDEX_NAME, doc_type=OFFICE_TYPE, id=office.siret, body=body, params={'ignore': 404})


def display_performance_stats(departement):
    methods = [
               '_get_score_from_hirings',
               'get_hirings_from_score',
               'get_score_adjusted_to_rome_code_and_naf_code',
              ]
    for method in methods:
        logging.info("[DPT%s] %s : %s", departement, method, getattr(scoring_util, method).cache_info())

    logging.info("[DPT%s] indexed %s of %s offices and %s score_for_rome",
        departement,
        st.indexed_office_count,
        st.office_count,
        st.office_score_for_rome_count
    )


def update_data(drop_indexes, enable_profiling, single_job, disable_parallel_computing):
    if single_job and not drop_indexes:
        raise Exception("This combination does not make sense.")

    if single_job:
        drop_and_create_index()
        create_offices_for_departement('57')
        return

    if drop_indexes:
        drop_and_create_index()
        create_offices(enable_profiling, disable_parallel_computing)
        create_job_codes()
        create_locations()

    # Upon requests received from employers we can add, remove or update offices.
    # This permits us to complete or overload the data provided by the importer.
    add_offices()
    remove_offices()
    update_offices()
    update_offices_geolocations()

def update_data_profiling_wrapper(drop_indexes, enable_profiling, single_job, disable_parallel_computing=False):
    if enable_profiling:
        logging.info("STARTED run with profiling")
        profiler = Profile()
        profiler.runctx(
            "update_data(drop_indexes, enable_profiling, single_job, disable_parallel_computing)",
            locals(),
            globals()
        )
        relative_filename = 'profiling_results/create_index_run.kgrind'
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_filename)
        convert(profiler.getstats(), filename)
        logging.info("COMPLETED run with profiling: exported profiling result as %s", filename)
    else:
        logging.info("STARTED run without profiling")
        update_data(drop_indexes, enable_profiling, single_job, disable_parallel_computing)
        logging.info("COMPLETED run without profiling")

def run():
    parser = argparse.ArgumentParser(
        description="Update elasticsearch data: offices, ogr_codes and locations.")
    parser.add_argument('-d', '--drop-indexes', dest='drop_indexes',
        help="Drop and recreate index from scratch.")
    parser.add_argument('-p', '--profile', dest='profile',
        help="Enable code performance profiling for later visualization with Q/KCacheGrind.")
    parser.add_argument('-s', '--single-job', dest='single_job',
        help="Disable parallel computing and run a single office indexing job (departement 57) and nothing else.")
    args = parser.parse_args()

    drop_indexes = (args.drop_indexes is not None)
    enable_profiling = (args.profile is not None)
    single_job = (args.single_job is not None)

    update_data_profiling_wrapper(drop_indexes, enable_profiling, single_job)


if __name__ == '__main__':
    run()
