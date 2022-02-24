import collections
import logging
from collections import OrderedDict
from datetime import datetime
from enum import auto, Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from astroid import decorators
from slugify import slugify

from labonneboite.common import hiring_type_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common import sorting, util
from labonneboite.common.es import Elasticsearch
from labonneboite.common.fetcher import Fetcher
from labonneboite.common.models import Office, OfficeResult
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

        self._distance_sort_index = None

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
        clone = self.__class__(**kwargs)
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

    def _get_office_count(self):
        query = self._build_elastic_search_query(omit_sort=True, omit_aggretation=True, omit_pagination=True)
        return self._count_offices_from_es(query)

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
        total_dpae = self.clone(hiring_type=hiring_type_util.DPAE)._get_office_count()

        total_alternance = self.clone(hiring_type=hiring_type_util.ALTERNANCE)._get_office_count()

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
            result, aggregations = self._fetch_offices()

        if self.office_count <= current_page_size and add_suggestions:

            # Suggest other jobs.
            # Build a flat list of all the alternative romes of all searched romes.
            alternative_rome_codes = [alt_rome for rome in self.romes for alt_rome in ROME_MOBILITIES[rome]]
            for rome in set(alternative_rome_codes) - set(self.romes):
                office_count = self.clone(romes=[rome])._get_office_count()
                self.alternative_rome_codes[rome] = office_count

            # Suggest other distances.
            last_count = 0
            for distance, distance_label in [(30, '30 km'), (50, '50 km'), (3000, 'France entière')]:
                office_count = self.clone(distance=distance)._get_office_count()
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

    def _fetch_offices(self) -> Tuple[OfficesType, AggregationsType]:
        query = self._build_elastic_search_query()

        offices, aggregations_raw = self._get_offices_from_es_and_db(query)

        # Extract aggregations
        aggregations: AggregationsType = {}
        if self.aggregate_by:
            if 'naf' in self.aggregate_by:
                aggregations['naf'] = self._aggregate_naf(aggregations_raw)
            if 'hiring_type' in self.aggregate_by:
                pass  # hiring_type cannot technically be aggregated and is thus processed at a later step
            if 'headcount' in self.aggregate_by:
                aggregations['headcount'] = self._aggregate_headcount(aggregations_raw)
            if 'distance' in self.aggregate_by:
                if self.distance == DISTANCE_FILTER_MAX:
                    aggregations['distance'] = self._aggregate_distance(aggregations_raw)

        return offices, aggregations

    @property
    def gps_available(self):
        return self.latitude is not None and self.longitude is not None

    def _build_elastic_search_query(self, omit_sort=False, omit_aggretation=False, omit_pagination=False):
        # Build filters.
        filters = self._build_es_query_filters()

        query: Dict = {"query": {"filtered": {"filter": {"bool": {"must": filters,}}}}}
        if not omit_sort:
            query = self._apply_sort(query)
        if not omit_aggretation:
            query = self._add_aggretation(query)
        if not omit_pagination:
            query = self._add_pagination(query)

        return query

    @decorators.cachedproperty
    def _distance_sort(self):

        distance_sort = {
            "_geo_distance": {
                "locations": {
                    "lat": self.latitude,
                    "lon": self.longitude,
                },
                "order": "asc",
                "unit": "km",
            }
        }

        return distance_sort

    def _apply_sort(self, main_query: Dict):

        main_query['sort'] = []

        # Build sorting.
        if self.sort == sorting.SORT_FILTER_SCORE:
            # always show boosted offices first then sort by randomized score
            self._add_boosted_romes_sort(main_query)
            self._add_score_sort(main_query)
            self._add_distance_sort(main_query)
        elif self.sort == sorting.SORT_FILTER_DISTANCE:
            self._add_distance_sort(main_query)

        return main_query

    def _add_boosted_romes_sort(self, main_query: Dict):
        # FIXME one day make boosted_rome logic compatible with multi rome, right now it only
        # works based on the first of the romes. Not urgent, as multi rome is API only,
        # and also this would increase complexity of the ES sorting mechanism.
        rome_code = self.romes[0]
        boosted_rome_field_name = self._get_boosted_rome_field_name(self.hiring_type, rome_code)

        boosted_romes_sort = {
            boosted_rome_field_name: {
                # offices without boost (missing field) are showed last
                "missing": "_last",
                # required, see
                # https://stackoverflow.com/questions/17051709/no-mapping-found-for-field-in-order-to-sort-on-in-elasticsearch
                "ignore_unmapped": True,
            }
        }
        main_query['sort'].append(boosted_romes_sort)
        return main_query

    def _add_score_sort(self, main_query: Dict):
        query = main_query.pop('query')

        query = self._use_max_score_for_rome(query)
        query = self._add_smart_randomization(query)

        # FTR we have contributed this ES weighted shuffling example to these posts:
        # https://stackoverflow.com/questions/34128770/weighted-random-sampling-in-elasticsearch
        # https://github.com/elastic/elasticsearch/issues/7783#issuecomment-64880008
        main_query['query'] = query
        main_query['sort'].append('_score')

        return main_query

    def _use_max_score_for_rome(self, main_query: Dict) -> Dict:
        """
        Overload main_query to get maximum score amongst all rome_codes.
        """

        query = {
            # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html
            "function_score": {
                "query": main_query,
                "functions": [
                    {
                        # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html#function-field-value-factor
                        "field_value_factor": {
                            "field": self._get_score_for_rome_field_name(self.hiring_type, rome_code),
                            "modifier": "none",
                            # Fallback value used in case the field score_for_rome_field_name is absent.
                            "missing": 0,
                        }
                    } for rome_code in self.romes
                ],
                # How to combine the result of the various functions 'field_value_factor' (1 per rome_code).
                # We keep the maximum score amongst scores of all requested rome_codes.
                "score_mode": "max",
                # How to combine the result of function_score with the original _score from the query.
                # We overwrite it as our combined _score == max(score_for_rome for rome in romes) is all we need.
                "boost_mode": "replace",
            }
        }
        return query

    def _add_smart_randomization(self, main_query: Dict) -> Dict:
        """
        Overload main_query to add smart randomization aka weighted shuffling aka "Tri optimisé"
        """

        query = {
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
        return query

        # FTR we have contributed this ES weighted shuffling example to these posts:
        # https://stackoverflow.com/questions/34128770/weighted-random-sampling-in-elasticsearch
        # https://github.com/elastic/elasticsearch/issues/7783#issuecomment-64880008
        main_query['query'] = random_score_query
        main_query['sort'].append('_score')

        return main_query

    def _add_distance_sort(self, main_query: Dict):
        if self.gps_available:
            main_query['sort'].append(
                self._distance_sort)  # required so that office distance can be extracted and displayed on frontend
        else:
            main_query['sort'].append({"department": {"order": "asc",}})

        self._distance_sort_index = len(main_query['sort']) - 1

        return main_query

    def _add_aggretation(self, json_body: Dict):
        # Add aggregate
        if self.aggregate_by:
            json_body['aggs'] = {}
            for aggregate in self.aggregate_by:
                # Distance is not an ES field, so we have to do a specific aggregation.
                if aggregate == 'distance' and self.gps_available:
                    json_body['aggs']['distance'] = {
                        'geo_distance': {
                            "field": "locations",
                            "origin": f"{self.latitude},{self.longitude}",
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

        return json_body

    def _add_pagination(self, json_body):
        # Process from_number and to_number.
        if self.from_number:
            json_body["from"] = self.from_number - 1
            if self.to_number:
                if self.to_number < self.from_number:
                    # this should never happen
                    logger.exception("to_number < from_number : %s < %s", self.to_number, self.from_number)
                    raise Exception("to_number < from_number")
                json_body["size"] = self.to_number - self.from_number + 1

        return json_body

    def _build_es_query_filters(self) -> Sequence[Filter]:
        filters: List[Filter] = []
        self._addFilterRange('score', gt=0, to=filters)
        self._addFilterTerms('naf', self.naf_codes, to=filters, if_=self.naf_codes)

        self._addHeadcountFilter(self.headcount, to=filters)

        self._addFilterTerm('flag_junior', to=filters, if_=self.flag_junior == 1)
        self._addFilterTerm('flag_senior', to=filters, if_=self.flag_senior == 1)
        self._addFilterTerm('flag_handicap', to=filters, if_=self.flag_handicap == 1)

        # at least one of these fields should exist
        self._unsureRomeIsInScores(self.romes, self.hiring_type, to=filters)

        if self.gps_available:
            filters.append({
                "geo_distance": {
                    "distance": "%skm" % self.distance,
                    "locations": {
                        "lat": self.latitude,
                        "lon": self.longitude,
                    }
                }
            })

        self._addFilterTerms('department', self.departments, to=filters, if_=self.departments)
        self._addFilterTerm('flag_pmsmp', 1, to=filters, if_=self.flag_pmsmp == 1)
        return filters

    def _get_offices_from_es_and_db(self, query) -> Tuple[Sequence[OfficeResult], Sequence[Dict]]:
        """
        Fetch offices first from Elasticsearch, then from the database.

        Returns a tuple of (offices, office_count), where `offices` is a
        list of results as Office instances (with some extra attributes only available
        in Elasticsearch) and `office_count` an integer of the results number.
        """
        assert self._distance_sort_index is not None

        es_res: Dict = self._get_offices_from_es(query)
        office_results: List[OfficeResult] = self._get_office_results_from_es_results(es_res)
        aggregations: Sequence[Dict] = es_res.get('aggregations', list())

        return office_results, aggregations

    def _get_office_results_from_es_results(self, es_res: Dict) -> Sequence[OfficeResult]:
        office_count: int = es_res['hits']['total']
        es_offices_by_siret: 'OrderedDict[str, Dict]' = self._es_office_to_office_by_siret(es_res)

        offices: List[Office] = self._get_offices_from_db(es_offices_by_siret)
        office_results: List[OfficeResult] = self._format_offices_in_office_results(
            offices,
            es_offices_by_siret,
            office_count,
        )

        return office_results

    def _get_offices_from_db(self, es_offices_by_siret: 'OrderedDict[str, Dict]') -> List[Office]:
        offices: List[Office] = []
        if es_offices_by_siret:
            office_objects: Iterable[Office] = Office.query.filter(Office.siret.in_(es_offices_by_siret.keys()))
            offices_by_siret: Dict[str, Office] = {office.siret: office for office in office_objects}
            contained_sirets: Iterable[str] = filter(offices_by_siret.__contains__, es_offices_by_siret.keys())
            sorted_offices: Iterable[Office] = map(offices_by_siret.get, contained_sirets)

            for office in sorted_offices:
                if office.has_city():
                    offices.append(office)
                else:
                    logging.info("office siret %s does not have city, ignoring...", siret)
        return offices

    def _get_offices_from_es(self, query) -> Dict:
        res: Dict
        es = Elasticsearch()
        logger.debug("Elastic Search request : %s", query)
        res = es.search(index=settings.ES_INDEX, doc_type="office", body=query)
        return res

    def _es_office_to_office_by_siret(self, es_res: Dict) -> 'OrderedDict[str, Dict]':
        es_offices_by_siret = OrderedDict((item['_source']['siret'], item) for item in es_res['hits']['hits'])
        return es_offices_by_siret

    def _get_rome_with_highest_score(self, es_office: Dict) -> Optional[str]:
        rome_with_highest_score: Optional[str] = None
        if len(self.romes) > 1:
            # Get self.romes actually matching this office.
            # Case of "contract=alternance"
            if self.hiring_type == hiring_type_util.ALTERNANCE:
                # beware: sometimes the key ALTERNANCE_SCORE_FIELD_NAME is in _source but equals None
                all_scores = es_office['_source'].get(ALTERNANCE_SCORE_FIELD_NAME, None) or {}
            else:
                all_scores = {}

            # Case of DPAE and alternance, keep the DPAE scores in both cases
            dpae_scores = es_office['_source'].get(DPAE_SCORE_FIELD_NAME, None)
            if dpae_scores:
                all_scores = {**dpae_scores, **all_scores}  # This will merge the 2 dicts

            scores_of_searched_romes = dict([(rome, all_scores[rome]) for rome in self.romes if rome in all_scores])

            # https://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
            rome_with_highest_score = max(scores_of_searched_romes, key=scores_of_searched_romes.get)
        elif self.romes:
            rome_with_highest_score = self.romes[0]
        return rome_with_highest_score

    def _format_offices_in_office_results(
        self,
        offices: Sequence[Office],
        es_offices_by_siret: Dict[str, Dict],
        office_count: int,
    ) -> Sequence[OfficeResult]:
        office_results: List[OfficeResult] = []

        # Check each office in the results and add some fields
        for position, office in enumerate(offices, start=1):
            result = OfficeResult(office, offers_count=office_count, position=position)

            # Get the corresponding item from the Elasticsearch results.
            es_office = es_offices_by_siret[office.siret]

            if len(es_office["sort"]) <= self._distance_sort_index:
                raise ValueError("Incorrect number of sorting fields in ES response.")

            # Add an extra `distance` attribute with one digit.
            if self.gps_available:
                result.distance = round(es_office["sort"][self._distance_sort_index], 1)

            # Set contact mode and position
            result.matched_rome = rome_with_highest_score = self._get_rome_with_highest_score(es_office)

            result.contact_mode = util.get_contact_mode_for_rome_and_office(rome_with_highest_score, office)

            # Set boost flag
            boosted_rome_keyname = self._get_boosted_rome_field_name(self.hiring_type, self.romes[0]).split('.')[0]
            boost_romes = es_office['_source'].get(boosted_rome_keyname, None)
            if boost_romes:
                romes_intersection = set(self.romes).intersection(boost_romes)
                result.boost = bool(romes_intersection)

            office_results.append(result)

        return office_results

    @staticmethod
    def _aggregate_naf(aggregations_raw) -> NafAggregationType:
        return [{
            "code": naf_aggregate['key'],
            "count": naf_aggregate['doc_count'],
            'label': settings.NAF_CODES.get(naf_aggregate['key']),
        } for naf_aggregate in aggregations_raw['naf']['buckets']]

    @staticmethod
    def _aggregate_headcount(aggregations_raw) -> HeadcountAggregationType:
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

    @staticmethod
    def _aggregate_distance(aggregations_raw) -> DistanceAggregationType:
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

    @staticmethod
    def _get_score_field_name(hiring_type: str):
        mapping = {
            hiring_type_util.DPAE: DPAE_SCORE_FIELD_NAME,
            hiring_type_util.ALTERNANCE: ALTERNANCE_SCORE_FIELD_NAME,
        }
        return mapping[hiring_type]

    @classmethod
    def _get_score_for_rome_field_name(cls, hiring_type: str, rome_code: str):
        field_name = cls._get_score_field_name(hiring_type)
        return f"{field_name}.{rome_code}"

    @staticmethod
    def _get_boosted_rome_field_name(hiring_type, rome_code):
        hiring_type = hiring_type or hiring_type_util.DEFAULT

        return {
            hiring_type_util.DPAE: "boosted_romes.%s",
            hiring_type_util.ALTERNANCE: "boosted_alternance_romes.%s",
        }[hiring_type] % rome_code

    @classmethod
    def _addFilterRange(cls, key: str, *, to: List[Filter], if_=True, **kwargs):
        cls._conditionallyAddFilter("range", key, kwargs, to=to, if_=if_)

    @classmethod
    def _addFilterTerms(cls, key: str, value: TermsType, *, to: List[Filter], if_=True):
        cls._conditionallyAddFilter("terms", key, value, to=to, if_=if_)

    @classmethod
    def _addFilterTerm(cls, key: str, value: TermType = 1, *, to: List[Filter], if_=True):
        cls._conditionallyAddFilter("term", key, value, to=to, if_=if_)

    @classmethod
    def _conditionallyAddFilter(cls, type_: str, key: str, value: ValueType, *, to: List[Filter], if_=True):
        if if_:
            cls._addFilter(type_, key, value, to=to)

    @staticmethod
    def _addFilter(type_: str, key: str, value: ValueType, *, to: List[Filter]):
        to.append({
            type_: {
                key: value
            },
        })

    @classmethod
    def _addHeadcountFilter(cls, headcount: Union[str, int], *, to: list):
        # in some cases, a string is given as input, let's ensure it is an int from now on
        try:
            headcount = int(headcount)
        except ValueError:
            headcount = settings.HEADCOUNT_WHATEVER

        cls._addFilterRange("headcount",
                            to=to,
                            lte=settings.HEADCOUNT_SMALL_ONLY_MAXIMUM,
                            if_=headcount == settings.HEADCOUNT_SMALL_ONLY)
        cls._addFilterRange("headcount",
                            to=to,
                            gte=settings.HEADCOUNT_BIG_ONLY_MINIMUM,
                            if_=headcount == settings.HEADCOUNT_BIG_ONLY)

    @classmethod
    def _unsureRomeIsInScores(cls, rome_codes: Sequence[str], hiring_type: str, to: list):
        to.append({
            "bool": {
                "should": [{
                    "exists": {
                        "field": cls._get_score_for_rome_field_name(hiring_type, rome_code),
                    }
                } for rome_code in rome_codes]
            }
        })
