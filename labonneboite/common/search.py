import collections
import logging
from datetime import datetime
from enum import auto, Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from slugify import slugify

from labonneboite.common import hiring_type_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common import sorting, util
from labonneboite.common.es import Elasticsearch
from labonneboite.common.fetcher import Fetcher
from labonneboite.common.models import Office
from labonneboite.common.pagination import OFFICES_PER_PAGE
from labonneboite.common.rome_mobilities import ROME_MOBILITIES
from labonneboite.conf import settings

logger = logging.getLogger('main')

unset = object()


class AudienceFilter(Enum):
    ALL = 0
    JUNIOR = 1
    SENIOR = 2
    HANDICAP = 3


TermType = Union[str, int]
TermsType = Sequence[TermType]
RangeType = Dict[str, int]
ValueType = Union[TermsType, TermType, RangeType]
Filter = Dict[str, Dict[str, Any]]

OfficeType = Dict
OfficesType = List[OfficeType]
NafAggregationType = List[Dict]
HeadcountAggregationType = Dict
DistanceAggregationType = Dict

AggregationType = Union[NafAggregationType, HeadcountAggregationType, DistanceAggregationType]
AggregationsType = Dict[str, AggregationType]

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
        departments=None,
        romes=None,
        distance=None,
        travel_mode=None,  # TODO: remove unused travel mode
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
        self.office_count = None
        self.latitude = latitude
        self.longitude = longitude

        self.romes = romes
        self.distance = distance
        self.travel_mode = travel_mode
        self.sort = sort or sorting.SORT_FILTER_DEFAULT
        assert self.sort in sorting.SORT_FILTERS, 'invalid sort type'
        self.hiring_type = hiring_type or hiring_type_util.DEFAULT
        assert self.hiring_type in hiring_type_util.VALUES, f'invalid hiring type {hiring_type!r}'

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

    def clone(self, **kwargs):
        kwargs.setdefault('longitude', self.longitude)
        kwargs.setdefault('latitude', self.latitude)
        kwargs.setdefault('departments', self.departments)
        kwargs.setdefault('romes', self.romes)
        kwargs.setdefault('distance', self.distance)
        kwargs.setdefault('travel_mode', self.travel_mode)
        kwargs.setdefault('sort', self.sort)
        kwargs.setdefault('hiring_type', self.hiring_type)
        kwargs.setdefault('from_number', self.from_number)
        kwargs.setdefault('to_number', self.to_number)
        kwargs.setdefault('audience', self.audience)
        kwargs.setdefault('headcount', self.headcount)
        kwargs.setdefault('naf', self.naf)
        kwargs.setdefault('naf_codes', self.naf_codes)
        kwargs.setdefault('aggregate_by', self.aggregate_by)
        kwargs.setdefault('flag_pmsmp', self.flag_pmsmp)
        clone = HiddenMarketFetcher(**kwargs)
        clone.office_count = self.office_count
        return clone

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

    def _get_office_count(self, rome_codes=unset, distance=unset, hiring_type=unset):
        rome_codes = rome_codes if rome_codes != unset else self.romes
        distance = distance if distance != unset else self.distance
        hiring_type = hiring_type if hiring_type != unset else self.hiring_type

        json_body = build_json_body_elastic_search(
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
            hiring_type=hiring_type,
            departments=self.departments,
            flag_pmsmp=self.flag_pmsmp,
            aggregate_by=None,
            sort=self.sort,
        )
        # Drop the sorting clause as it is not needed anyway for a simple count.
        del json_body["sort"]
        return self._count_offices_from_es(json_body)

    @staticmethod
    def _count_offices_from_es(json_body):
        es = Elasticsearch()
        res = es.count(index=settings.ES_INDEX, doc_type="office", body=json_body)
        return res["count"]

    def get_naf_aggregations(self):
        clone = self.clone(
            naf_codes={},  # No naf filter
            aggregate_by=["naf"],  # Only naf aggregate
        )
        _, aggregations = clone.get_offices()
        return aggregations['naf']

    def get_headcount_aggregations(self):
        clone = self.clone(
            aggregate_by=["headcount"],  # Only headcount aggregate
            headcount=settings.HEADCOUNT_WHATEVER,  # No headcount filter
        )
        _, aggregations = clone.get_offices()
        return aggregations['headcount']

    def get_contract_aggregations(self):
        """
        As contract/hiring_type (dpae/alternance) is not technically a filter,
        we cannot do a regular aggregation about it. Instead we manually
        do two ES calls everytime.
        """
        total_dpae = self._get_office_count(hiring_type=hiring_type_util.DPAE)

        total_alternance = self._get_office_count(hiring_type=hiring_type_util.ALTERNANCE)

        return {'alternance': total_alternance, 'dpae': total_dpae}

    def get_distance_aggregations(self):
        clone = self.clone(
            distance=DISTANCE_FILTER_MAX,  # France
            aggregate_by=["distance"],
        )
        _, aggregations = clone.get_offices()
        return aggregations['distance']

    def compute_office_count(self):
        self.office_count = self._get_office_count()
        logger.debug("set office_count to %s", self.office_count)

    def get_offices(self, add_suggestions=False) -> Tuple[OfficesType, AggregationsType]:
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

        result: OfficesType = []
        aggregations: AggregationsType = {}
        if self.office_count:
            result, _, aggregations = self._fetch_offices()

        if self.office_count <= current_page_size and add_suggestions:

            # Suggest other jobs.
            # Build a flat list of all the alternative romes of all searched romes.
            alternative_rome_codes = [alt_rome for rome in self.romes for alt_rome in ROME_MOBILITIES[rome]]
            for rome in set(alternative_rome_codes) - set(self.romes):
                office_count = self._get_office_count(rome_codes=[rome])
                self.alternative_rome_codes[rome] = office_count

            # Suggest other distances.
            last_count = 0
            for distance, distance_label in [(30, '30 km'), (50, '50 km'), (3000, 'France entière')]:
                office_count = self._get_office_count(distance=distance)
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


    def _fetch_offices(self) -> Tuple[OfficesType, int, AggregationsType]:
        aggregate_by = self.aggregate_by
        distance = self.distance
        sort = self.sort or sorting.SORT_FILTER_DEFAULT

        json_body = build_json_body_elastic_search(self.naf_codes,
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
                                                aggregate_by=self.aggregate_by)

        offices, office_count, aggregations_raw = get_offices_from_es_and_db(
            json_body,
            sort=self.sort,
            rome_codes=self.romes,
            hiring_type=self.hiring_type,
        )

        # Extract aggregations
        aggregations: AggregationsType = {}
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


def aggregate_naf(aggregations_raw) -> NafAggregationType:
    return [{
        "code": naf_aggregate['key'],
        "count": naf_aggregate['doc_count'],
        'label': settings.NAF_CODES.get(naf_aggregate['key']),
    } for naf_aggregate in aggregations_raw['naf']['buckets']]


def aggregate_headcount(aggregations_raw) -> HeadcountAggregationType:
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


def aggregate_distance(aggregations_raw) -> DistanceAggregationType:
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


def get_score_field_name(hiring_type: str):
    mapping = {
        hiring_type_util.DPAE: DPAE_SCORE_FIELD_NAME,
        hiring_type_util.ALTERNANCE: ALTERNANCE_SCORE_FIELD_NAME,
    }
    return mapping[hiring_type]


def get_score_for_rome_field_name(hiring_type: str, rome_code: str):
    field_name = get_score_field_name(hiring_type)
    return f"{field_name}.{rome_code}"


def get_boosted_rome_field_name(hiring_type, rome_code):
    hiring_type = hiring_type or hiring_type_util.DEFAULT

    return {
        hiring_type_util.DPAE: "boosted_romes.%s",
        hiring_type_util.ALTERNANCE: "boosted_alternance_romes.%s",
    }[hiring_type] % rome_code


def addFilterRange(key: str, *, to: List[Filter], if_=True, **kwargs):
    conditionallyAddFilter("range", key, kwargs, to=to, if_=if_)


def addFilterTerms(key: str, value: TermsType, *, to: List[Filter], if_=True):
    conditionallyAddFilter("terms", key, value, to=to, if_=if_)


def addFilterTerm(key: str, value: TermType = 1, *, to: List[Filter], if_=True):
    conditionallyAddFilter("term", key, value, to=to, if_=if_)


def conditionallyAddFilter(type_: str, key: str, value: ValueType, *, to: List[Filter], if_=True):
    if if_:
        addFilter(type_, key, value, to=to)


def addFilter(type_: str, key: str, value: ValueType, *, to: List[Filter]):
    to.append({
        type_: {
            key: value
        },
    })


def addHeadcountFilter(headcount: Union[str, int], *, to: list):
    # in some cases, a string is given as input, let's ensure it is an int from now on
    try:
        headcount = int(headcount)
    except ValueError:
        headcount = settings.HEADCOUNT_WHATEVER

    addFilterRange("headcount",
                   to=to,
                   lte=settings.HEADCOUNT_SMALL_ONLY_MAXIMUM,
                   if_=headcount == settings.HEADCOUNT_SMALL_ONLY)
    addFilterRange("headcount",
                   to=to,
                   gte=settings.HEADCOUNT_BIG_ONLY_MINIMUM,
                   if_=headcount == settings.HEADCOUNT_BIG_ONLY)


def unsureRomeIsInScores(rome_codes: Sequence[str], hiring_type: str, to: list):
    to.append({
        "bool": {
            "should": [{
                "exists": {
                    "field": get_score_for_rome_field_name(hiring_type, rome_code),
                }
            } for rome_code in rome_codes]
        }
    })


def buildFilters(
    naf_codes: Sequence[str],
    rome_codes: Sequence[str],
    latitude: Optional[float],
    longitude: Optional[float],
    distance: str,
    headcount: int,
    hiring_type: Optional[str],
    flag_junior: int,
    flag_senior: int,
    flag_handicap: int,
    departments: Optional[TermsType],
    flag_pmsmp: Optional[int],
    gps_available: bool,
) -> List[Filter]:
    filters: List[Filter] = []
    addFilterRange('score', gt=0, to=filters)
    addFilterTerms('naf', naf_codes, to=filters, if_=naf_codes)

    addHeadcountFilter(headcount, to=filters)

    addFilterTerm('flag_junior', to=filters, if_=flag_junior == 1)
    addFilterTerm('flag_senior', to=filters, if_=flag_senior == 1)
    addFilterTerm('flag_handicap', to=filters, if_=flag_handicap == 1)

    # at least one of these fields should exist
    unsureRomeIsInScores(rome_codes, hiring_type, to=filters)

    if gps_available:
        filters.append(
            {"geo_distance": {
                "distance": "%skm" % distance,
                "locations": {
                    "lat": latitude,
                    "lon": longitude,
                }
            }})

    addFilterTerms('department', departments, to=filters, if_=departments)
    addFilterTerm('flag_pmsmp', 1, to=filters, if_=flag_pmsmp == 1)
    return filters


def build_json_body_elastic_search(
    naf_codes: Sequence[str],
    rome_codes: Sequence[str],
    latitude: Optional[float],
    longitude: Optional[float],
    distance: str,
    travel_mode=None,  # todo: remove
    from_number: Optional[int] = None,
    to_number: Optional[int] = None,
    headcount: int = settings.HEADCOUNT_WHATEVER,
    sort: str = sorting.SORT_FILTER_DEFAULT,
    hiring_type: Optional[str] = None,
    flag_junior: int = 0,
    flag_senior: int = 0,
    flag_handicap: int = 0,
    aggregate_by: Sequence[str] = None,
    departments: Optional[Sequence[str]] = None,
    flag_pmsmp: Optional[int] = None,
):

    hiring_type = hiring_type or hiring_type_util.DEFAULT
    gps_available = latitude is not None and longitude is not None

    # Build filters.
    filters = buildFilters(
        naf_codes,
        rome_codes,
        latitude,
        longitude,
        distance,
        headcount,
        hiring_type,
        flag_junior,
        flag_senior,
        flag_handicap,
        departments,
        flag_pmsmp,
        gps_available,
    )

    main_query: Dict = {"filtered": {"filter": {"bool": {"must": filters,}}}}

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
                            "field": get_score_for_rome_field_name(hiring_type, rome_code),
                            "modifier": "none",
                            # Fallback value used in case the field score_for_rome_field_name is absent.
                            "missing": 0,
                        }
                    } for rome_code in rome_codes
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

    sort_attrs: List[Any] = []

    if sort == sorting.SORT_FILTER_SCORE:
        # FIXME one day make boosted_rome logic compatible with multi rome, right now it only
        # works based on the first of the romes. Not urgent, as multi rome is API only,
        # and also this would increase complexity of the ES sorting mechanism.
        rome_code = rome_codes[0]
        boosted_rome_field_name = get_boosted_rome_field_name(hiring_type, rome_code)

        boosted_romes_sort = {
            boosted_rome_field_name: {
                # offices without boost (missing field) are showed last
                "missing": "_last",
                # required, see
                # https://stackoverflow.com/questions/17051709/no-mapping-found-for-field-in-order-to-sort-on-in-elasticsearch
                "ignore_unmapped": True,
            }
        }

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

    json_body: Dict = {
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
                        "origin": f"{latitude},{longitude}",
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


def get_offices_from_es_and_db(json_body, sort: str, rome_codes: Sequence[str], hiring_type: str):
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
