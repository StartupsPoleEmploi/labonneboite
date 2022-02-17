from datetime import datetime
import collections
import logging

from enum import auto, Enum
from slugify import slugify

from labonneboite.common import mapping as mapping_util
from labonneboite.common import sorting
from labonneboite.common import hiring_type_util
from labonneboite.common import util
from labonneboite.common.pagination import OFFICES_PER_PAGE
from labonneboite.common.models import Office
from labonneboite.common.fetcher import Fetcher
from labonneboite.common.es import Elasticsearch
from labonneboite.conf import settings
from labonneboite.common.rome_mobilities import ROME_MOBILITIES

logger = logging.getLogger('main')


class AudienceFilter(Enum):
    ALL = 0
    JUNIOR = 1
    SENIOR = 2
    HANDICAP = 3


KEY_TO_LABEL_DISTANCES = {
    '*-10.0': 'less_10_km',
    '*-30.0': 'less_30_km',
    '*-50.0': 'less_50_km',
    '*-100.0': 'less_100_km',
    '*-3000.0': 'france',
}

FILTERS = ['naf', 'headcount', 'hiring_type', 'distance']
DISTANCE_FILTER_MAX = 3000

DPAE_SCORE_FIELD_NAME = 'scores_by_rome'
ALTERNANCE_SCORE_FIELD_NAME = 'scores_alternance_by_rome'


class HiddenMarketFetcher(Fetcher):
    """
    Fetch offices having a high hiring potential whether or not they
    have public job offers.
    """

    def __init__(
        self,
        longitude,
        latitude,
        departments,
        romes=None,
        distance=None,
        travel_mode=None,
        sort=None,
        hiring_type=None,
        from_number=1,
        to_number=OFFICES_PER_PAGE,
        audience=None,
        headcount=None,
        naf=None,
        naf_codes=None,
        aggregate_by=None,
        flag_pmsmp=None,
    ):
        self.latitude = latitude
        self.longitude = longitude

        self.romes = romes
        self.distance = distance
        self.travel_mode = travel_mode
        self.sort = sort
        self.hiring_type = hiring_type

        # Pagination.
        self.from_number = from_number
        self.to_number = to_number

        # Flags.
        self.audience = audience

        # Headcount.
        try:
            self.headcount = int(headcount)
        except (TypeError, ValueError):
            self.headcount = settings.HEADCOUNT_WHATEVER

        # Empty list is needed to handle offices with ROME not related to their NAF
        self.naf = naf
        self.naf_codes = naf_codes or {}
        if self.naf and not self.naf_codes:
            self.naf_codes = mapping_util.map_romes_to_nafs(self.romes, [self.naf])

        # Aggregate_by
        self.aggregate_by = aggregate_by

        # Other properties.
        self.alternative_rome_codes = {}
        self.alternative_distances = collections.OrderedDict()
        self.office_count = None
        self.departments = departments
        self.flag_pmsmp = flag_pmsmp

    @property
    def flag_handicap(self):
        return self.audience == AudienceFilter.HANDICAP

    @property
    def flag_junior(self):
        return self.audience == AudienceFilter.JUNIOR

    @property
    def flag_senior(self):
        return self.audience == AudienceFilter.SENIOR

    def update_aggregations(self, aggregations):
        if self.headcount and 'headcount' in aggregations:
            aggregations['headcount'] = self.get_headcount_aggregations()
        if self.distance != DISTANCE_FILTER_MAX and 'distance' in aggregations:
            aggregations['distance'] = self.get_distance_aggregations()
        if self.naf and 'naf' in aggregations:
            aggregations['naf'] = self.get_naf_aggregations()

    def _get_office_count(self, rome_codes, distance):
        return count_offices(
            self.naf_codes,
            rome_codes,
            self.latitude,
            self.longitude,
            distance,
            travel_mode=self.travel_mode,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            hiring_type=self.hiring_type,
            departments=self.departments,
            flag_pmsmp=self.flag_pmsmp,
            aggregate_by=None,
            sort=self.sort,
        )

    def get_naf_aggregations(self):
        _, _, aggregations = fetch_offices(
            {},  # No naf filter
            self.romes,
            self.latitude,
            self.longitude,
            self.distance,
            travel_mode=self.travel_mode,
            aggregate_by=["naf"],  # Only naf aggregate
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            hiring_type=self.hiring_type,
            departments=self.departments,
            flag_pmsmp=self.flag_pmsmp,
        )
        return aggregations['naf']

    def get_headcount_aggregations(self):
        _, _, aggregations = fetch_offices(
            self.naf_codes,
            self.romes,
            self.latitude,
            self.longitude,
            self.distance,
            travel_mode=self.travel_mode,
            aggregate_by=["headcount"],  # Only headcount aggregate
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=settings.HEADCOUNT_WHATEVER,  # No headcount filter
            hiring_type=self.hiring_type,
            departments=self.departments,
            flag_pmsmp=self.flag_pmsmp,
        )
        return aggregations['headcount']

    def get_contract_aggregations(self):
        """
        As contract/hiring_type (dpae/alternance) is not technically a filter,
        we cannot do a regular aggregation about it. Instead we manually
        do two ES calls everytime.
        """
        total_dpae = count_offices(
            self.naf_codes,
            self.romes,
            self.latitude,
            self.longitude,
            self.distance,
            travel_mode=self.travel_mode,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            hiring_type=hiring_type_util.DPAE,
            departments=self.departments,
            flag_pmsmp=self.flag_pmsmp,
        )

        total_alternance = count_offices(
            self.naf_codes,
            self.romes,
            self.latitude,
            self.longitude,
            self.distance,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            hiring_type=hiring_type_util.ALTERNANCE,
            departments=self.departments,
            flag_pmsmp=self.flag_pmsmp,
        )

        return {'alternance': total_alternance, 'dpae': total_dpae}

    def get_distance_aggregations(self):
        _, _, aggregations = fetch_offices(
            self.naf_codes,
            self.romes,
            self.latitude,
            self.longitude,
            DISTANCE_FILTER_MAX,  # France
            travel_mode=self.travel_mode,
            aggregate_by=["distance"],
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            hiring_type=self.hiring_type,
            departments=self.departments,
            flag_pmsmp=self.flag_pmsmp,
        )
        return aggregations['distance']

    def compute_office_count(self):
        self.office_count = self._get_office_count(self.romes, self.distance)
        logger.debug("set office_count to %s", self.office_count)

    def get_offices(self, add_suggestions=False):
        self.compute_office_count()

        current_page_size = self.to_number - self.from_number + 1

        # Needed in rare case when an old page is accessed (via user bookmark and/or crawling bot)
        # which no longer exists due to newer office dataset having less result pages than before
        # for this search.
        if self.from_number > self.office_count:
            self.from_number = 1
            self.to_number = current_page_size

        # Adjustement needed when the last page is requested and does not have exactly page_size items.
        if self.to_number > self.office_count + 1:
            self.to_number = self.office_count + 1

        result = {}
        aggregations = {}
        if self.office_count:
            result, _, aggregations = fetch_offices(
                self.naf_codes,
                self.romes,
                self.latitude,
                self.longitude,
                self.distance,
                travel_mode=self.travel_mode,
                from_number=self.from_number,
                to_number=self.to_number,
                flag_junior=self.flag_junior,
                flag_senior=self.flag_senior,
                flag_handicap=self.flag_handicap,
                headcount=self.headcount,
                sort=self.sort,
                hiring_type=self.hiring_type,
                departments=self.departments,
                flag_pmsmp=self.flag_pmsmp,
                aggregate_by=self.aggregate_by,
            )

        if self.office_count <= current_page_size and add_suggestions:

            # Suggest other jobs.
            # Build a flat list of all the alternative romes of all searched romes.
            alternative_rome_codes = [alt_rome for rome in self.romes for alt_rome in ROME_MOBILITIES[rome]]
            for rome in set(alternative_rome_codes) - set(self.romes):
                office_count = self._get_office_count([rome], self.distance)
                self.alternative_rome_codes[rome] = office_count

            # Suggest other distances.
            last_count = 0
            for distance, distance_label in [(30, '30 km'), (50, '50 km'), (3000, 'France entière')]:
                office_count = self._get_office_count(self.romes, distance)
                if office_count > last_count:
                    last_count = office_count
                    self.alternative_distances[distance] = (distance_label, last_count)

        return result, aggregations

    def get_alternative_rome_descriptions(self):
        alternative_rome_descriptions = []
        for alternative, count in self.alternative_rome_codes.items():
            if settings.ROME_DESCRIPTIONS.get(alternative) and count:
                desc = settings.ROME_DESCRIPTIONS.get(alternative)
                slug = slugify(desc)
                alternative_rome_descriptions.append([alternative, desc, slug, count])
        return alternative_rome_descriptions


def count_offices(naf_codes, rome_codes, latitude, longitude, distance, **kwargs):
    json_body = build_json_body_elastic_search(naf_codes, rome_codes, latitude, longitude, distance, **kwargs)
    # Drop the sorting clause as it is not needed anyway for a simple count.
    del json_body["sort"]
    return count_offices_from_es(json_body)


def count_offices_from_es(json_body):
    es = Elasticsearch()
    res = es.count(index=settings.ES_INDEX, doc_type="office", body=json_body)
    return res["count"]


def fetch_offices(naf_codes, rome_codes, latitude, longitude, distance, aggregate_by=None, **kwargs):
    json_body = build_json_body_elastic_search(naf_codes,
                                               rome_codes,
                                               latitude,
                                               longitude,
                                               distance,
                                               aggregate_by=aggregate_by,
                                               **kwargs)

    sort = kwargs.get('sort', sorting.SORT_FILTER_DEFAULT)

    offices, office_count, aggregations_raw = get_offices_from_es_and_db(
        json_body,
        sort=sort,
        rome_codes=rome_codes,
        hiring_type=kwargs['hiring_type'],
    )

    # Extract aggregations
    aggregations = {}
    if aggregate_by:
        if 'naf' in aggregate_by:
            aggregations['naf'] = aggregate_naf(aggregations_raw)
        if 'hiring_type' in aggregate_by:
            pass  # hiring_type cannot technically be aggregated and is thus processed at a later step
        if 'headcount' in aggregate_by:
            aggregations['headcount'] = aggregate_headcount(aggregations_raw)
        if 'distance' in aggregate_by:
            if distance == DISTANCE_FILTER_MAX:
                aggregations['distance'] = aggregate_distance(aggregations_raw)

    return offices, office_count, aggregations


def aggregate_naf(aggregations_raw):
    return [{
        "code": naf_aggregate['key'],
        "count": naf_aggregate['doc_count'],
        'label': settings.NAF_CODES.get(naf_aggregate['key']),
    } for naf_aggregate in aggregations_raw['naf']['buckets']]


def aggregate_headcount(aggregations_raw):
    small = 0
    big = 0

    # Count by HEADCOUNT_INSEE values
    for contract_aggregate in aggregations_raw["headcount"]["buckets"]:
        key = contract_aggregate['key']
        if key <= settings.HEADCOUNT_SMALL_ONLY_MAXIMUM:
            small += contract_aggregate['doc_count']
        elif key >= settings.HEADCOUNT_BIG_ONLY_MINIMUM:
            big += contract_aggregate['doc_count']

    return {'small': small, 'big': big}


def aggregate_distance(aggregations_raw):
    distances_aggregations = {}
    for distance_aggregate in aggregations_raw['distance']['buckets']:
        key = distance_aggregate['key']
        try:
            label = KEY_TO_LABEL_DISTANCES[key]
        except KeyError as e:
            # Unknown distance aggregation key
            logger.exception(e)
            continue

        distances_aggregations[label] = distance_aggregate['doc_count']

    return distances_aggregations


def get_score_for_rome_field_name(hiring_type, rome_code):
    return {
        hiring_type_util.DPAE: DPAE_SCORE_FIELD_NAME + ".%s",
        hiring_type_util.ALTERNANCE: ALTERNANCE_SCORE_FIELD_NAME + ".%s",
    }[hiring_type] % rome_code


def get_boosted_rome_field_name(hiring_type, rome_code):
    hiring_type = hiring_type or hiring_type_util.DEFAULT

    return {
        hiring_type_util.DPAE: "boosted_romes.%s",
        hiring_type_util.ALTERNANCE: "boosted_alternance_romes.%s",
    }[hiring_type] % rome_code


def build_json_body_elastic_search(
    naf_codes,
    rome_codes,
    latitude,
    longitude,
    distance,
    travel_mode=None,
    from_number=None,
    to_number=None,
    headcount=settings.HEADCOUNT_WHATEVER,
    sort=sorting.SORT_FILTER_DEFAULT,
    hiring_type=None,
    flag_junior=0,
    flag_senior=0,
    flag_handicap=0,
    aggregate_by=None,
    departments=None,
    flag_pmsmp=None,
):

    hiring_type = hiring_type or hiring_type_util.DEFAULT
    gps_available = latitude is not None and longitude is not None

    if hiring_type == hiring_type_util.DPAE or settings.ALTERNANCE_SEARCH_MODE == 'ONLY_ALTERNANCE_COMPANIES':
        # Case of a search for DPAE **or** ALTERNANCE companies
        score_for_rome_field_names = [get_score_for_rome_field_name(hiring_type, rome_code) for rome_code in rome_codes]
    else:
        # Case of a search for DPAE **and** ALTERNANCE companies
        score_for_rome_field_names = [
            get_score_for_rome_field_name(h_type, r_code)
            for h_type, r_code in [(h_type, r_code) for h_type in hiring_type_util.VALUES for r_code in rome_codes]
        ]

    # FIXME one day make boosted_rome logic compatible with multi rome, right now it only
    # works based on the first of the romes. Not urgent, as multi rome is API only,
    # and also this would increase complexity of the ES sorting mechanism.
    rome_code = rome_codes[0]
    boosted_rome_field_name = get_boosted_rome_field_name(hiring_type, rome_code)

    # Build filters.
    filters = [{"range": {"score": {"gt": 0,}}}]
    should_filters = []
    if naf_codes:
        filters = [{
            "terms": {
                "naf": naf_codes,
            },
        }]

    # in some cases, a string is given as input, let's ensure it is an int from now on
    try:
        headcount = int(headcount)
    except ValueError:
        headcount = settings.HEADCOUNT_WHATEVER

    max_office_size = None
    min_office_size = None
    if headcount == settings.HEADCOUNT_SMALL_ONLY:
        max_office_size = settings.HEADCOUNT_SMALL_ONLY_MAXIMUM
    elif headcount == settings.HEADCOUNT_BIG_ONLY:
        min_office_size = settings.HEADCOUNT_BIG_ONLY_MINIMUM

    if min_office_size or max_office_size:
        if min_office_size:
            headcount = {"gte": min_office_size}
        if max_office_size:
            headcount = {"lte": max_office_size}
        filters.append({"numeric_range": {"headcount": headcount,}})

    if flag_junior == 1:
        filters.append({"term": {"flag_junior": 1,}})

    if flag_senior == 1:
        filters.append({"term": {"flag_senior": 1,}})

    if flag_handicap == 1:
        filters.append({"term": {"flag_handicap": 1,}})

    # at least one of these fields should exist
    filters.append(
        {"bool": {
            "should": [{
                "exists": {
                    "field": field_name,
                }
            } for field_name in score_for_rome_field_names]
        }})

    if gps_available:
        filters.append(
            {"geo_distance": {
                "distance": "%skm" % distance,
                "locations": {
                    "lat": latitude,
                    "lon": longitude,
                }
            }})

    if departments:
        filters.append({'terms': {'department': departments,}})

    if flag_pmsmp == 1:
        filters.append({"term": {"flag_pmsmp": 1,}})

    main_query = {"filtered": {"filter": {"bool": {"must": filters,}}}}

    if should_filters:
        # 'should' filters means that at least 1 of the filters should match
        main_query['filtered']['filter']['bool']['should'] = should_filters

    # Build sorting.

    if sort == sorting.SORT_FILTER_SCORE:

        # 1) overload main_query to get maximum score amongst all rome_codes
        main_query = {
            # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html
            "function_score": {
                "query": main_query,
                "functions": [
                    {
                        # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html#function-field-value-factor
                        "field_value_factor": {
                            "field": score_for_rome_field_name,
                            "modifier": "none",
                            # Fallback value used in case the field score_for_rome_field_name is absent.
                            "missing": 0,
                        }
                    } for score_for_rome_field_name in score_for_rome_field_names
                ],
                # How to combine the result of the various functions 'field_value_factor' (1 per rome_code).
                # We keep the maximum score amongst scores of all requested rome_codes.
                "score_mode": "max",
                # How to combine the result of function_score with the original _score from the query.
                # We overwrite it as our combined _score == max(score_for_rome for rome in romes) is all we need.
                "boost_mode": "replace",
            }
        }

        # 2) overload main_query to add smart randomization aka weighted shuffling aka "Tri optimisé"
        main_query = {
            # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html
            "function_score": {
                "query": main_query,
                "functions": [
                    {
                        "random_score": {
                            # Use a different seed every day. This way results are shuffled again
                            # every 24 hours.
                            "seed": datetime.today().strftime('%Y-%m-%d'),
                        },
                    },
                ],
                # How to combine the result of the various functions.
                # Totally irrelevant here as we use only one function.
                "score_mode": "multiply",
                # How to combine the result of function_score with the original _score from the query.
                # We multiply so that our final _score = (random x max(score_for_rome for rome in romes)).
                # This way, on average the combined _score of a office having score 100 will be 5 times as much
                # as the combined _score of a office having score 20, and thus will be 5 times more likely
                # to appear on first page.
                "boost_mode": "multiply",
            }
        }

        # FTR we have contributed this ES weighted shuffling example to these posts:
        # https://stackoverflow.com/questions/34128770/weighted-random-sampling-in-elasticsearch
        # https://github.com/elastic/elasticsearch/issues/7783#issuecomment-64880008

    if sort not in sorting.SORT_FILTERS:
        logger.info('unknown sort: %s', sort)
        sort = sorting.SORT_FILTER_DEFAULT

    distance_sort = {
        "_geo_distance": {
            "locations": {
                "lat": latitude,
                "lon": longitude,
            },
            "order": "asc",
            "unit": "km",
        }
    }

    boosted_romes_sort = {
        boosted_rome_field_name: {
            # offices without boost (missing field) are showed last
            "missing": "_last",
            # required, see
            # https://stackoverflow.com/questions/17051709/no-mapping-found-for-field-in-order-to-sort-on-in-elasticsearch
            "ignore_unmapped": True,
        }
    }

    sort_attrs = []

    if sort == sorting.SORT_FILTER_SCORE:
        # always show boosted offices first then sort by randomized score
        sort_attrs.append(boosted_romes_sort)
        randomized_score_sort = "_score"
        sort_attrs.append(randomized_score_sort)
        if gps_available:
            sort_attrs.append(
                distance_sort)  # required so that office distance can be extracted and displayed on frontend
        else:
            sort_attrs.append({"department": {"order": "asc",}})

    elif sort == sorting.SORT_FILTER_DISTANCE:
        # no randomization nor boosting happens when sorting by distance
        sort_attrs.append(distance_sort)

    json_body = {
        "sort": sort_attrs,
        "query": main_query,
    }

    # Add aggregate
    if aggregate_by:
        json_body['aggs'] = {}
        for aggregate in aggregate_by:
            # Distance is not an ES field, so we have to do a specific aggregation.
            if aggregate == 'distance' and gps_available:
                json_body['aggs']['distance'] = {
                    'geo_distance': {
                        "field": "locations",
                        "origin": "%s,%s" % (latitude, longitude),
                        'unit': 'km',
                        'ranges': [{
                            'to': 10
                        }, {
                            'to': 30
                        }, {
                            'to': 50
                        }, {
                            'to': 100
                        }, {
                            'to': 3000
                        }],
                    }
                }
            # We cannot use aggregation for contract=dpae/alternance, as both kinds use different
            # logics and are not simply two different values of the same field.
            elif aggregate == 'contract':
                pass
            else:
                json_body['aggs'][aggregate] = {"terms": {"field": aggregate,}}

    # Process from_number and to_number.
    if from_number:
        json_body["from"] = from_number - 1
        if to_number:
            if to_number < from_number:
                # this should never happen
                logger.exception("to_number < from_number : %s < %s", to_number, from_number)
                raise Exception("to_number < from_number")
            json_body["size"] = to_number - from_number + 1

    return json_body


def get_offices_from_es_and_db(json_body, sort, rome_codes, hiring_type):
    """
    Fetch offices first from Elasticsearch, then from the database.

    Returns a tuple of (offices, office_count), where `offices` is a
    list of results as Office instances (with some extra attributes only available
    in Elasticsearch) and `office_count` an integer of the results number.

    `sort` is needed to find back the distance between each office and the search location,
    to store it and display it later on the frontend or in the API result.

    `rome_codes` and `hiring_type` are needed in the case of multi rome search, to find
    back for each office which rome_code actually did match.
    """
    if sort not in sorting.SORT_FILTERS:
        # This should never happen.
        # An API request would have already raised a InvalidFetcherArgument exception,
        # and a Frontend request would have fallbacked to default sorting.
        raise ValueError("unknown sorting : %s" % sort)

    es = Elasticsearch()
    logger.debug("Elastic Search request : %s", json_body)
    res = es.search(index=settings.ES_INDEX, doc_type="office", body=json_body)

    office_count = res['hits']['total']
    offices = []
    siret_list = [office["_source"]["siret"] for office in res['hits']['hits']]

    if siret_list:

        office_objects = Office.query.filter(Office.siret.in_(siret_list))
        office_dict = {obj.siret: obj for obj in office_objects}

        for siret in siret_list:
            try:
                office = office_dict[siret]
            except KeyError:
                # ES and DB out of sync: siret is in ES but not in DB - this should never happen
                logger.error("ES and DB out of sync: siret %s is in ES but not in DB - this should never happen", siret)
                raise
            if office.has_city():
                offices.append(office)
            else:
                logging.info("office siret %s does not have city, ignoring...", siret)

    # FIXME it's not great to add new properties to an existing object. It
    # would be better to wrap the office objects in a new OfficeResult
    # class that would add new properties related to the query.
    es_offices_by_siret = {item['_source']['siret']: item for item in res['hits']['hits']}
    # FIXME These hardcoded values are soooooo ugly, unfortunately it is not so
    # easy to make it DNRY. For the corresponding code see method build_json_body_elastic_search().
    distance_sort_index = {
        sorting.SORT_FILTER_DISTANCE: 0,
        sorting.SORT_FILTER_SCORE: 2,
    }[sort]
    sort_fields_total = {
        sorting.SORT_FILTER_DISTANCE: 1,  # (distance_sort)
        sorting.SORT_FILTER_SCORE: 3,  # (boosted_romes_sort, randomized_score_sort, distance_sort)
    }[sort]
    # Check each office in the results and add some fields
    for position, office in enumerate(offices, start=1):
        # Get the corresponding item from the Elasticsearch results.
        es_office = es_offices_by_siret[office.siret]

        if len(es_office["sort"]) != sort_fields_total:
            raise ValueError("Incorrect number of sorting fields in ES response.")
        # Check if this is a request with long/lat
        has_geo_distance = any([('_geo_distance' in d) for d in json_body.get('sort')])
        # Add an extra `distance` attribute with one digit.
        if has_geo_distance:
            office.distance = round(es_office["sort"][distance_sort_index], 1)
        # position is later used in labonneboite/web/static/js/results.js
        office.position = position

        if len(rome_codes) > 1:
            # Get rome_codes actually matching this office.
            # Case of "contract=alternance"
            if hiring_type == hiring_type_util.ALTERNANCE:
                # beware: sometimes the key ALTERNANCE_SCORE_FIELD_NAME is in _source but equals None
                all_scores = es_office['_source'].get(ALTERNANCE_SCORE_FIELD_NAME, None) or {}
            else:
                all_scores = {}

            # Case of DPAE and alternance, keep the DPAE scores in both cases
            dpae_scores = es_office['_source'].get(DPAE_SCORE_FIELD_NAME, None)
            if dpae_scores:
                all_scores = {**dpae_scores, **all_scores}  # This will merge the 2 dicts

            scores_of_searched_romes = dict([(rome, all_scores[rome]) for rome in rome_codes if rome in all_scores])

            # https://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
            rome_with_highest_score = max(scores_of_searched_romes, key=scores_of_searched_romes.get)
            # Store it as an extra attribute.
            office.matched_rome = rome_with_highest_score
            rome_code_for_contact_mode = rome_with_highest_score
        else:
            rome_code_for_contact_mode = rome_codes[0]

        # Set boost flag
        office.boost = False
        boosted_rome_keyname = get_boosted_rome_field_name(hiring_type, rome_codes[0]).split('.')[0]
        boost_romes = es_office['_source'].get(boosted_rome_keyname, None)
        if boost_romes:
            romes_intersection = set(rome_codes).intersection(boost_romes)
            office.boost = bool(romes_intersection)

        # Set contact mode and position
        office.contact_mode = util.get_contact_mode_for_rome_and_office(rome_code_for_contact_mode, office)

    try:
        aggregations = res['aggregations']
    except KeyError:
        aggregations = []

    return offices, office_count, aggregations
