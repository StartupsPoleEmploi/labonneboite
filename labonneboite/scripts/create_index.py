import argparse
import contextlib
import datetime
import glob
import logging
import multiprocessing as mp
import os
import time
from cProfile import Profile
from typing import Dict, Optional, Union, List, Type, Generator, Any, Tuple

from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch.helpers import bulk
from labonneboite_common import departements as dpt
from labonneboite_common import encoding as encoding_util
from labonneboite_common.models.office_mixin import OfficeMixin
from pyprof2calltree import convert
from sqlalchemy import and_, inspect
from sqlalchemy.exc import OperationalError
import sqlalchemy as sa

from labonneboite.conf import settings
from labonneboite.common import es, geocoding, hiring_type_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common import pdf as pdf_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common.chunks import chunks
from labonneboite.common.database import db_session
from labonneboite.common.load_data import load_ogr_labels, load_siret_to_remove, OGR_ROME_CODES
from labonneboite.common.models import HistoryBlacklist, Office, OfficeAdminAdd, OfficeAdminExtraGeoLocation, \
    OfficeAdminRemove, OfficeAdminUpdate, OfficeThirdPartyUpdate
from labonneboite.common.search import HiddenMarketFetcher
from labonneboite.common.util import timeit
from labonneboite.importer import settings as importer_settings
from labonneboite.importer import util as importer_util

logging.basicConfig(level=logging.INFO, format='%(message)s')
# use this instead if you wish to investigate from which logger exactly comes each line of log
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERBOSE_LOGGER_NAMES = ['elasticsearch', 'sqlalchemy.engine.base.Engine', 'main', 'elasticsearch.trace']

ES_BULK_CHUNK_SIZE = 10000  # default value is 500

PSE_STUDY_IS_ENABLED = False


class Profiling(object):
    ACTIVATED = False


@contextlib.contextmanager
def switch_es_index() -> Generator[None, None, None]:
    """
    Context manager that will ensure that some code will operate on a new ES
    index. This new index will then be associated to the reference alias and
    the old index(es) will be dropped.

    Usage:

        with switch_es_index():
            # Here, all code will run on the new index
            run_some_code()

        # Here, the old indexes no longer exist and the reference alias points
        # to the new index
    """
    # Find current index names (there may be one, zero or more)
    alias_name = settings.ES_INDEX
    try:
        old_index_names = list(es.Elasticsearch().indices.get_alias(settings.ES_INDEX).keys())
    except NotFoundError:
        old_index_names = []

    # Activate new index
    new_index_name = es.get_new_index_name()
    settings.ES_INDEX = new_index_name

    # Create new index
    es.create_index(new_index_name)

    try:
        yield
    except Exception:
        # Delete newly created index
        es.drop_index(new_index_name)
        raise
    finally:
        # Set back alias name
        settings.ES_INDEX = alias_name

    # Switch alias
    # TODO this should be done in one shot with a function in es.py module
    es.add_alias_to_index(new_index_name)
    for old_index_name in old_index_names:
        es.Elasticsearch().indices.delete_alias(index=old_index_name, name=alias_name)

    # Delete old index
    for old_index_name in old_index_names:
        es.drop_index(old_index_name)


def get_verbose_loggers() -> List['logging.Logger']:
    return [logging.getLogger(logger_name) for logger_name in VERBOSE_LOGGER_NAMES]


def disable_verbose_loggers() -> None:
    """
    We disable some loggers at specific points of this script in order to have a clean output
    (especially of the sanity_check_rome_codes part) and avoid it being polluted by useless
    unwanted logs detailing every MysQL and ES request.
    """
    for verbose_logger in get_verbose_loggers():
        # For some unknown reason, logger.setLevel(logging.ERROR) here does not work as expected as
        # 'INFO' level messages are still visible. Hence we brutally disable the logger instead.
        # FIXME try again to increase logger level instead of disabling it.
        verbose_logger.disabled = True


def enable_verbose_loggers() -> None:
    for verbose_logger in get_verbose_loggers():
        verbose_logger.disabled = False


class Counter(object):
    """
    Counter class without the race-condition bug.
    Needed to be able to have a variable (counter) shared between all parallel jobs.
    Inspired from https://stackoverflow.com/questions/2080660/python-multiprocessing-and-a-shared-counter
    """

    def __init__(self) -> None:
        self.val = mp.Value('i', 0)

    def increment(self, n: int = 1) -> None:
        with self.val.get_lock():
            self.val.value += n

    @property
    def value(self) -> int:
        return self.val.value  # type: ignore


completed_jobs_counter = Counter()


class StatTracker:

    def __init__(self) -> None:
        self.office_count = 0
        self.indexed_office_count = 0
        self.office_score_for_rome_count = 0
        self.office_score_alternance_for_rome_count = 0

    def increment_office_count(self) -> None:
        self.office_count += 1

    def increment_indexed_office_count(self) -> None:
        self.indexed_office_count += 1

    def increment_office_score_for_rome_count(self) -> None:
        self.office_score_for_rome_count += 1

    def increment_office_score_alternance_for_rome_count(self) -> None:
        self.office_score_alternance_for_rome_count += 1


st = StatTracker()


def bulk_actions(actions: List[Dict[str, Any]]) -> None:
    # unfortunately parallel_bulk is not available in the current elasticsearch version
    # http://elasticsearch-py.readthedocs.io/en/master/helpers.html
    logger.info("started bulk of %s actions...", len(actions))
    # each parallel job needs to use its own ES connection for maximum performance
    bulk(es.new_elasticsearch_instance(), actions, chunk_size=ES_BULK_CHUNK_SIZE)
    logger.info("completed bulk of %s actions!", len(actions))


@timeit
def create_job_codes() -> None:
    """
    Create the `ogr` type in ElasticSearch.
    """
    logger.info("create job codes...")
    # libelles des appelations pour les codes ROME
    ogr_labels = load_ogr_labels()
    # correspondance appellation vers rome
    ogr_rome_codes = OGR_ROME_CODES
    actions = []

    for ogr, description in ogr_labels.items():
        if ogr in ogr_rome_codes:
            rome_code = ogr_rome_codes[ogr]
            rome_description = settings.ROME_DESCRIPTIONS[rome_code]
            doc = {
                'ogr_code': ogr,
                'ogr_description': description,
                'rome_code': rome_code,
                'rome_description': rome_description
            }
            action = {'_op_type': 'index', '_index': settings.ES_INDEX, '_type': es.OGR_TYPE, '_source': doc}
            actions.append(action)
    bulk_actions(actions)


@timeit
def create_locations() -> None:
    """
    Create the `location` type in ElasticSearch.
    """
    actions = []
    for city in geocoding.get_cities():
        doc = {
            'city_name': city['name'],
            'location': {
                'lat': city['coords']['lat'],
                'lon': city['coords']['lon']
            },
            'population': city['population'],
            'slug': city['slug'],
            'zipcode': city['zipcode'],
        }
        action = {'_op_type': 'index', '_index': settings.ES_INDEX, '_type': es.LOCATION_TYPE, '_source': doc}
        actions.append(action)

    bulk_actions(actions)


def get_office_as_es_doc(
        office: OfficeMixin
) -> Dict[str, Union[int, str, None, List[Dict[str, int]], Dict[str, int], Dict[str, bool]]]:
    """
    Return the office as a JSON document suitable for indexation in ElasticSearch.
    The `office` parameter can be an `Office` or an `OfficeAdminAdd` instance.
    """
    # The `headcount` field of an `OfficeAdminAdd` instance has a `code` attribute.
    if hasattr(office.headcount, 'code'):
        headcount = office.headcount.code  # type: ignore
    else:
        headcount = office.headcount

    try:
        headcount = int(headcount)
    except (ValueError, TypeError):
        headcount = 0

    # Cleanup exotic characters.
    sanitized_name = encoding_util.sanitize_string(office.office_name)
    sanitized_email = encoding_util.sanitize_string(office.email)
    sanitized_website = encoding_util.sanitize_string(office.website)

    doc = {
        'naf': office.naf,
        'siret': office.siret,
        'score': office.score,
        'hiring': office.hiring,
        'score_alternance': office.score_alternance,
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
        'flag_pmsmp': int(office.flag_pmsmp),
    }

    if office.y and office.x:
        # Use an array to allow multiple locations per document, see https://goo.gl/fdTaEM
        # Multiple locations may be added later via the admin UI.
        doc['locations'] = [
            {
                'lat': office.y,
                'lon': office.x
            },
        ]

    scores_by_rome, boosted_romes = get_scores_by_rome_and_boosted_romes(office)
    if scores_by_rome:
        doc['scores_by_rome'] = scores_by_rome
        doc['boosted_romes'] = boosted_romes

    return doc


def get_scores_by_rome_and_boosted_romes(
        office: OfficeMixin,
        office_to_update: Optional[Union[OfficeAdminUpdate, OfficeThirdPartyUpdate]] = None
) -> Tuple[Dict[str, int], Dict[str, bool]]:
    # 0 - Get all romes related to the company

    # fetch all rome_codes mapped to the naf of this office
    # as we will compute a score adjusted for each of them
    office_nafs = [office.naf]
    # Handle NAFs added to a company
    if office_to_update:
        office_nafs += office_to_update.as_list(office_to_update.nafs_to_add)

    scores_by_rome: Dict[str, int] = {}
    # elasticsearch does not understand sets, so we use a dict of 'key => True' instead
    boosted_romes: Dict[str, bool] = {}

    if PSE_STUDY_IS_ENABLED:
        sirets_to_remove_pse = load_siret_to_remove()
        office_to_remove_pse = (office.siret in sirets_to_remove_pse)
    else:
        office_to_remove_pse = False

    for naf in office_nafs:
        try:
            naf_rome_codes = mapping_util.get_romes_for_naf(naf)
        except KeyError:
            # unfortunately some NAF codes have no matching ROME at all
            continue

        # 1- DPAE

        romes_to_boost = []
        romes_to_remove = []
        if office_to_update:
            romes_to_boost = office_to_update.as_list(office_to_update.romes_to_boost)
            romes_to_remove = office_to_update.as_list(office_to_update.romes_to_remove)

        # Add unrelated rome for indexing (with boost) and remove unwanted romes
        rome_codes = set(naf_rome_codes).union(set(romes_to_boost)) - set(romes_to_remove)

        for rome_code in rome_codes:
            # Manage office boosting - DPAE
            if office_to_update and office_to_update.boost:
                if not office_to_update.romes_to_boost:
                    # Boost the score for all ROME codes.
                    boosted_romes[rome_code] = True
                elif rome_code in romes_to_boost:
                    # Boost the score for some ROME codes only.
                    boosted_romes[rome_code] = True

            # Scoring part
            score_dpae = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(hiring=office.hiring,
                                                                                   rome_code=rome_code,
                                                                                   naf_code=naf)

            # Get the score minimum for a rome code with metiers en tension
            score_minimum_for_rome = scoring_util.get_score_minimum_for_rome(rome_code)

            if (score_dpae >= score_minimum_for_rome or rome_code in boosted_romes):
                if office_to_remove_pse:
                    # 0 as a special score for PSE companies ensures they
                    # always show up *last* in the results, even after
                    # results randomization
                    score_dpae = 0
                if rome_code in scores_by_rome:
                    # this ROME was already computed before for another NAF
                    if score_dpae > scores_by_rome[rome_code]:
                        # keep highest score for this rome among all possible NAF codes
                        scores_by_rome[rome_code] = score_dpae
                else:
                    scores_by_rome[rome_code] = score_dpae
                    st.increment_office_score_for_rome_count()

    return scores_by_rome, boosted_romes


def create_offices(disable_parallel_computing: bool = False) -> None:
    """
    Populate the `office` type in ElasticSearch.
    Run it as a parallel computation based on departements.
    """
    if Profiling.ACTIVATED:
        func = profile_create_offices_for_departement
    else:
        func = create_offices_for_departement

    if disable_parallel_computing:
        for departement in dpt.DEPARTEMENTS:
            func(departement)
    else:
        # Use parallel computing on all available CPU cores.
        # Use even slightly more than avaible CPUs because in practise a job does not always
        # use 100% of a cpu.
        # maxtasksperchild default is infinite, which means memory is never freed up, and grows indefinitely :-/
        # maxtasksperchild=1 ensures memory is freed up after every departement computation.
        pool = mp.Pool(processes=int(1.25 * mp.cpu_count()), maxtasksperchild=1)
        pool.map(func, dpt.DEPARTEMENTS)
        pool.close()
        pool.join()


@timeit
def create_offices_for_departement(departement: str) -> None:
    """
    Populate the `office` type in ElasticSearch with offices having given departement.
    """
    actions = []

    logger.info("STARTED indexing offices for departement=%s ...", departement)

    # For LBB we apply two thresholds to show an office:
    # 1) its global all-rome-included score should be at least SCORE_REDUCING_MINIMUM_THRESHOLD
    # 2) its score adapted to requested rome should be at least SCORE_FOR_ROME_MINIMUM
    # For LBA we only apply the second threshold (SCORE_ALTERNANCE_FOR_ROME_MINIMUM)
    # and no longer apply the all-rome-included score threshold, in order to include
    # more relevant smaller companies.
    all_offices = db_session.query(Office).filter(
        and_(
            # Office.departement == departement,
            Office.hiring >= importer_settings.HIRING_REDUCING_MINIMUM_THRESHOLD,
        )).all()

    for office in all_offices:
        st.increment_office_count()

        es_doc = get_office_as_es_doc(office)

        office_is_reachable = ('scores_by_rome' in es_doc) or ('scores_alternance_by_rome' in es_doc)

        if office_is_reachable:
            st.increment_indexed_office_count()
            actions.append({
                '_op_type': 'index',
                '_index': settings.ES_INDEX,
                '_type': es.OFFICE_TYPE,
                '_id': office.siret,
                '_source': es_doc,
            })

    bulk_actions(actions)

    completed_jobs_counter.increment()

    logger.info(
        "COMPLETED indexing offices for departement=%s (%s of %s jobs completed)",
        departement,
        completed_jobs_counter.value,
        len(dpt.DEPARTEMENTS),
    )

    display_performance_stats(departement)


def profile_create_offices_for_departement(departement: str) -> None:
    """
    Run create_offices_for_departement with profiling.
    """
    profiler: Profile = Profile()
    command = "create_offices_for_departement('%s')" % departement
    profiler.runctx(command, locals(), globals())
    relative_filename = 'profiling_results/create_index_dpt%s.kgrind' % departement
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_filename)
    convert(profiler.getstats(), filename)  # type: ignore


@timeit
def add_offices() -> None:
    """
    Add offices (complete the data provided by the importer).
    """
    office_to_add: OfficeAdminAdd
    for office_to_add in db_session.query(OfficeAdminAdd).all():

        office = Office.query.filter_by(siret=office_to_add.siret).first()

        # Only create a new office if it does not already exist.
        # This guarantees that the importer data will always have precedence.
        if not office:

            # The `headcount` field of an `OfficeAdminAdd` instance has a `code` attribute.
            if hasattr(office_to_add.headcount, 'code'):
                headcount = office_to_add.headcount.code  # type: ignore
            else:
                headcount = office_to_add.headcount
            # Create the new office in DB.
            new_office = Office()
            # Use `inspect` because `Office` columns are named distinctly from attributes.
            for field_name in list(inspect(Office).columns.keys()):
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
            es.Elasticsearch().create(index=settings.ES_INDEX,
                                      doc_type=es.OFFICE_TYPE,
                                      id=office_to_add.siret,
                                      body=doc)


def remove_individual_office(siret: str) -> None:
    # Apply changes in ElasticSearch.
    try:
        es.Elasticsearch().delete(index=settings.ES_INDEX, doc_type=es.OFFICE_TYPE, id=siret)
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
def remove_offices() -> None:
    """
    Remove offices (overload the data provided by the importer).
    """
    # When returning multiple rows, the SQLAlchemy Query class can only give them out as tuples.
    # We need to unpack them explicitly.
    offices_to_remove = [siret for (siret,) in db_session.query(OfficeAdminRemove.siret).all()]

    for siret in offices_to_remove:
        remove_individual_office(siret)


LIMIT = 100


def to_iterator(
        qry: 'sa.orm.query.Query[Union[OfficeAdminUpdate, OfficeThirdPartyUpdate]]',
        key: 'sa.Column[sa.Integer]'
) -> Generator[Union[OfficeAdminUpdate, OfficeThirdPartyUpdate], None, None]:
    """
    This function comes from this doc: https://github.com/sqlalchemy/sqlalchemy/wiki/RangeQuery-and-WindowedRangeQuery
    Specialized windowed query generator (using LIMIT/OFFSET)
    This recipe is to select through a large number of rows thats too
    large to fetch at once. The technique depends on the primary key
    of the FROM clause being an integer value, and selects items
    using LIMIT.
    """
    firstid = None
    while True:
        q = qry
        if firstid is not None:
            q = qry.filter(key > firstid)
        rec = None
        for rec in q.order_by(key).limit(LIMIT):
            yield rec
        if rec is None:
            break
        firstid = key.__get__(rec, key) if rec else None


@timeit
def update_offices(table: Union[Type[OfficeAdminUpdate], Type[OfficeThirdPartyUpdate]]) -> None:
    """
    Update offices (overload the data provided by the importer).
    """
    # Good engineering eliminates users being able to do the wrong thing as much as possible.
    # But since it is possible to store multiple SIRETs, there is no longer any constraint of uniqueness
    # on a SIRET. As a result, it shouldn't but there may be `n` entries in `table`
    # for the same SIRET. We order the query by creation date ASC so that the most recent changes take
    # priority over any older ones.
    for office_to_update in to_iterator(db_session.query(table), table.id):  # type: ignore

        for siret in table.as_list(office_to_update.sirets):

            office: Office = Office.query.filter_by(siret=siret).first()

            if office:
                is_updated = False
                # Apply changes in DB.
                # , "email", "tel", "website"
                if office_to_update.new_company_name and office.company_name != office_to_update.new_company_name:
                    office.company_name = office_to_update.new_company_name
                    is_updated = True
                if office_to_update.new_office_name and office.office_name != office_to_update.new_office_name:
                    office.office_name = office_to_update.new_office_name
                    is_updated = True
                offices_attributes = [
                    "email_alternance", "phone_alternance", "website_alternance", "hiring", "score_alternance",
                    "social_network", "contact_mode"
                ]
                update_attributes = [
                    "email_alternance", "phone_alternance", "website_alternance", "hiring", "score_alternance",
                    "social_network", "contact_mode"
                ]
                for office_attr, update_attr in list(zip(offices_attributes, update_attributes)):
                    if getattr(office, office_attr) != getattr(office_to_update, update_attr) and getattr(
                            office_to_update, update_attr) is not None:
                        setattr(office, office_attr, getattr(office_to_update, update_attr))
                        is_updated = True

                if office_to_update.remove_phone:
                    if office.tel != '':
                        office.tel = ''
                        is_updated = True
                else:
                    if office.tel != office_to_update.new_phone:
                        office.tel = office_to_update.new_phone
                        is_updated = True

                for attr in ["email", "website"]:
                    if getattr(office_to_update, f"remove_{attr}"):
                        if getattr(office, attr) != '':
                            setattr(office, attr, '')
                            is_updated = True
                    else:
                        if getattr(office, attr) != getattr(office_to_update, f"new_{attr}"):
                            setattr(office, attr, getattr(office_to_update, f"new_{attr}"))
                            is_updated = True

                if is_updated:
                    office.save()

                    # Apply changes in ElasticSearch.
                    body = {
                        'doc': {
                            'email': office.email,
                            'phone': office.tel,
                            'website': office.website,
                            "score": office.score,
                            'flag_alternance': 1 if office.flag_alternance else 0
                        }
                    }

                    scores_by_rome, boosted_romes = get_scores_by_rome_and_boosted_romes(office, office_to_update)
                    if scores_by_rome:
                        body['doc']['scores_by_rome'] = scores_by_rome
                        body['doc']['boosted_romes'] = boosted_romes

                    # The update API makes partial updates: existing `scalar` fields are overwritten,
                    # but `objects` fields are merged together.
                    # https://www.elastic.co/guide/en/elasticsearch/guide/1.x/partial-updates.html
                    # However `scores_by_rome` and `boosted_romes` need to be overwritten because they
                    # may change over time.
                    # To do this, we perform 2 requests: the first one resets `scores_by_rome` and
                    # `boosted_romes` and the second one populates them.
                    delete_body = {
                        'doc': {
                            'scores_by_rome': None,
                            'boosted_romes': None,
                            'scores_alternance_by_rome': None,
                            'boosted_alternance_romes': None
                        }
                    }

                    # Unfortunately these cannot easily be bulked :-(
                    # The reason is there is no way to tell bulk to ignore missing documents (404)
                    # for a partial update. Tried it and failed it on Oct 2017 @vermeer.
                    es.Elasticsearch().update(index=settings.ES_INDEX,
                                              doc_type=es.OFFICE_TYPE,
                                              id=siret,
                                              body=delete_body,
                                              params={'ignore': 404})
                    es.Elasticsearch().update(index=settings.ES_INDEX,
                                              doc_type=es.OFFICE_TYPE,
                                              id=siret,
                                              body=body,
                                              params={'ignore': 404})

                    # Delete the current PDF thus it will be regenerated at the next download attempt.
                    pdf_util.delete_file(office)


@timeit
def update_offices_geolocations() -> None:
    """
    Remove or add extra geolocations to offices.
    New geolocations are entered into the system through the `OfficeAdminExtraGeoLocation` table.
    """
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
            es.Elasticsearch().update(
                index=settings.ES_INDEX,
                doc_type=es.OFFICE_TYPE,
                id=office.siret,
                body=body,
                params={'ignore': 404},
            )


def get_latest_scam_emails() -> List[str]:
    list_of_files = glob.glob(os.path.join(settings.SCAM_EMAILS_FOLDER, 'lbb_blacklist_full_*.bz2'))
    if not list_of_files:
        raise ValueError("No blacklist file found. Path is most likely incorrect.")
    latest_file = max(list_of_files, key=os.path.getctime)
    with importer_util.get_reader(latest_file) as myfile:
        logger.info("Processing scam emails file %s ...", latest_file)
        myfile.readline()  # ignore header
        emails = [email.decode().strip().replace('"', '') for email in myfile]
        emails = [email for email in emails if email != '']
    logger.info("The emails file contains {} emails".format(len(emails)))
    return emails


@timeit
def remove_scam_emails() -> None:
    scam_emails = get_latest_scam_emails()
    for scam_emails_chunk in chunks(scam_emails, 100):
        query = Office.query.filter(Office.email.in_(scam_emails_chunk))
        office_count = query.count()
        if office_count:
            history = []
            for office in query.all():
                history.append(HistoryBlacklist(email=office.email, datetime_removal=datetime.datetime.now()))
            db_session.add_all(history)
            query.update({Office.email: ''}, synchronize_session="fetch")
            db_session.commit()
        logger.info(
            "Removed a chunk of %d scam emails from %d offices.",
            len(scam_emails_chunk),
            office_count,
        )


@timeit
def sanity_check_rome_codes() -> None:
    ogr_rome_mapping = OGR_ROME_CODES
    rome_labels = settings.ROME_DESCRIPTIONS
    rome_naf_mapping = mapping_util.MANUAL_ROME_NAF_MAPPING

    romes_from_ogr_rome_mapping = set(ogr_rome_mapping.values())
    romes_from_rome_labels = set(rome_labels.keys())
    romes_from_rome_naf_mapping = set(rome_naf_mapping.keys())

    subset1 = romes_from_ogr_rome_mapping - romes_from_rome_labels
    subset2 = romes_from_rome_labels - romes_from_ogr_rome_mapping
    subset3 = romes_from_rome_naf_mapping - romes_from_rome_labels
    subset4 = romes_from_rome_labels - romes_from_rome_naf_mapping

    msg = """
        -------------- SANITY CHECK ON ROME CODES --------------
        found %s distinct rome_codes in romes_from_ogr_rome_mapping
        found %s distinct rome_codes in romes_from_rome_labels
        found %s distinct rome_codes in romes_from_rome_naf_mapping

        found %s rome_codes present in romes_from_ogr_rome_mapping but not in romes_from_rome_labels: %s

        found %s rome_codes present in romes_from_rome_labels but not in romes_from_ogr_rome_mapping: %s

        found %s rome_codes present in romes_from_rome_naf_mapping but not in romes_from_rome_labels: %s

        found %s rome_codes present in romes_from_rome_labels but not in romes_from_rome_naf_mapping: %s
        """ % (
        len(romes_from_ogr_rome_mapping),
        len(romes_from_rome_labels),
        len(romes_from_rome_naf_mapping),
        len(subset1),
        subset1,
        len(subset2),
        subset2,
        len(subset3),
        subset3,
        len(subset4),
        # CSV style output for easier manipulation afterwards
        "".join(["\n%s|%s" % (r, rome_labels[r]) for r in subset4]),
    )
    logger.info(msg)

    city = geocoding.get_city_by_commune_id('75056')
    latitude = city['coords']['lat']
    longitude = city['coords']['lon']
    distance = 1000

    # CSV style output for easier manipulation afterwards
    logger.info("rome_id|rome_label|offices_in_france")
    for rome_id in romes_from_rome_naf_mapping:
        naf_code_list = mapping_util.map_romes_to_nafs([rome_id])
        disable_verbose_loggers()
        fetcher = HiddenMarketFetcher(
            naf_codes=naf_code_list,
            romes=[rome_id],
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            from_number=1,
            to_number=10,
            hiring_type=hiring_type_util.DPAE,
        )
        offices, _ = fetcher.get_offices()
        enable_verbose_loggers()
        if len(offices) < 5:
            logger.info("%s|%s|%s", rome_id, rome_labels[rome_id], len(offices))


def display_performance_stats(departement: str) -> None:
    methods = [
        '_get_score_from_hirings',
        'get_hirings_from_score',
        'get_score_adjusted_to_rome_code_and_naf_code',
    ]
    for method in methods:
        logger.info("[DPT%s] %s : %s", departement, method, getattr(scoring_util, method).cache_info())

    logger.info(
        "[DPT%s] indexed %s of %s offices and %s score_for_rome and %s scores_alternance_by_rome",
        departement,
        st.indexed_office_count,
        st.office_count,
        st.office_score_for_rome_count,
        st.office_score_alternance_for_rome_count,
    )


def update_data(create_full: bool, create_partial: bool, disable_parallel_computing: bool) -> None:
    logger.info("[update data] Creation of ES index")
    if create_partial:
        with switch_es_index():
            create_offices_for_departement('57')
        return

    if create_full:
        with switch_es_index():
            create_offices(disable_parallel_computing)
            create_job_codes()
            create_locations()

    # Upon requests received from employers we can add, remove or update offices.
    # This permits us to complete or overload the data provided by the importer.
    logger.info("[update data] Add offices (SAVE)")
    add_offices()
    logger.info("[update data] Remove offices (SAVE)")
    remove_offices()
    logger.info("[update data] Update offices (SAVE)")
    update_offices(OfficeAdminUpdate)
    logger.info("[update data] Update offices (third party)")
    update_offices(OfficeThirdPartyUpdate)

    # update_offices_geolocations()

    logger.info("[update data] Remove scam emails")
    remove_scam_emails()

    if create_full:
        logger.info("[update data] Sanity check rome codes")
        sanity_check_rome_codes()


def update_data_profiling_wrapper(create_full: bool, create_partial: bool,
                                  disable_parallel_computing: bool = False) -> None:
    if Profiling.ACTIVATED:
        logger.info("STARTED run with profiling")
        profiler = Profile()
        profiler.runctx("update_data(create_full, create_partial, disable_parallel_computing)", locals(), globals())
        relative_filename = 'profiling_results/create_index_run.kgrind'
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_filename)
        convert(profiler.getstats(), filename)  # type: ignore
        logger.info("COMPLETED run with profiling: exported profiling result as %s", filename)
    else:
        logger.info("STARTED run without profiling")
        update_data(create_full, create_partial, disable_parallel_computing)
        logger.info("COMPLETED run without profiling")


def run() -> None:
    parser = argparse.ArgumentParser(description="Update elasticsearch data: offices, ogr_codes and locations.")
    parser.add_argument('-f', '--full', action='store_true', help="Create full index from scratch.")
    parser.add_argument('-a',
                        '--partial',
                        action='store_true',
                        help=("Disable parallel computing and run only a single office indexing"
                              " job (departement 57) instead. This is required in order"
                              " to do a profiling from inside a job."))
    parser.add_argument('-p',
                        '--profile',
                        action='store_true',
                        help="Enable code performance profiling for later visualization with Q/KCacheGrind.")
    args = parser.parse_args()

    if args.full and args.partial:
        raise ValueError('Cannot create both partial and full index at the same time')
    if args.profile:
        Profiling.ACTIVATED = True

    update_data_profiling_wrapper(args.full, args.partial)


if __name__ == '__main__':
    run()
