# coding: utf8

from datetime import datetime
import collections
import itertools
import logging
import random
import unidecode

from elasticsearch import Elasticsearch
from slugify import slugify

from labonneboite.common import geocoding
from labonneboite.common import mapping as mapping_util
from labonneboite.common import sorting
from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.common.rome_mobilities import ROME_MOBILITIES

logger = logging.getLogger('main')


PUBLIC_ALL = 0
PUBLIC_JUNIOR = 1
PUBLIC_SENIOR = 2
PUBLIC_HANDICAP = 3
PUBLIC_CHOICES = [PUBLIC_ALL, PUBLIC_JUNIOR, PUBLIC_SENIOR, PUBLIC_HANDICAP]

KEY_TO_LABEL_DISTANCES = {
    u'*-10.0': u'less_10_km',
    u'*-30.0': u'less_30_km',
    u'*-50.0': u'less_50_km',
    u'*-100.0': u'less_100_km',
    u'*-3000.0': u'france',
}

FILTERS = ['naf', 'headcount', 'flag_alternance', 'distance']
DISTANCE_FILTER_MAX = 3000


class Location(object):
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return "lon: {} - lat: {}".format(self.longitude, self.latitude)


class CityLocation(object):

    def __init__(self, slug, zipcode):
        self.slug = slug
        self.zipcode = zipcode
        # Location attribute may be None if slug/zipcode combination is incorrect
        self.location = None

        city = geocoding.get_city_by_zipcode(self.zipcode, self.slug)
        if not city:
            logger.debug("unable to retrieve a city for zipcode `%s` and slug `%s`", self.zipcode, self.slug)
        else:
            coordinates = city['coords']
            self.location = Location(coordinates['lat'], coordinates['lon'])

    @property
    def is_location_correct(self):
        return self.location is not None

    @property
    def name(self):
        return self.slug.replace('-', ' ').capitalize()

    @property
    def full_name(self):
        return '%s (%s)' % (self.name, self.zipcode)


class Fetcher(object):

    def __init__(self, search_location, rome=None, distance=None, sort=None,
                 from_number=1, to_number=10, flag_alternance=None,
                 public=None, headcount=None, naf=None, naf_codes=None,
                 aggregate_by=None, departments=None, **kwargs):
        """
        This constructor takes many arguments; the goal is to reduce this list
        and to never rely on kwargs.

        Args:
            search_location (Location)
        """
        self.location = search_location

        self.rome = rome
        self.distance = distance
        self.sort = sort

        # Pagination.
        self.from_number = from_number
        self.to_number = to_number

        # Flags.
        self.flag_alternance = flag_alternance
        self.public = public

        # Headcount.
        try:
            self.headcount = int(headcount)
        except (TypeError, ValueError):
            self.headcount = settings.HEADCOUNT_WHATEVER

        # Empty list is needed to handle companies with ROME not related to their NAF
        self.naf = naf
        self.naf_codes = naf_codes or {}
        if self.naf and not self.naf_codes:
            self.naf_codes = mapping_util.map_romes_to_nafs([self.rome], [self.naf])

        # Aggregate_by
        self.aggregate_by = aggregate_by

        # Other properties.
        self.alternative_rome_codes = {}
        self.alternative_distances = collections.OrderedDict()
        self.company_count = None
        self.departments = departments

    @property
    def flag_handicap(self):
        return self.public == PUBLIC_HANDICAP
    @property
    def flag_junior(self):
        return self.public == PUBLIC_JUNIOR
    @property
    def flag_senior(self):
        return self.public == PUBLIC_SENIOR

    def update_aggregations(self, aggregations):
        if self.headcount and 'headcount' in aggregations:
            aggregations['headcount'] = self.get_headcount_aggregations()
        if self.flag_alternance and 'flag_alternance' in aggregations:
            aggregations['contract'] = self.get_headcount_aggregations()
        if self.distance != DISTANCE_FILTER_MAX and 'distance' in aggregations:
            aggregations['distance'] = self.get_distance_aggregations()
        if self.naf and 'naf' in aggregations:
            aggregations['naf'] = self.get_naf_aggregations()

    def _get_company_count(self, rome_code, distance):

        return count_companies(
            self.naf_codes,
            rome_code,
            self.location.latitude,
            self.location.longitude,
            distance,
            flag_alternance=self.flag_alternance,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            departments=self.departments,
            aggregate_by=None,
        )

    def get_naf_aggregations(self):
        _, _, aggregations = fetch_companies(
            {}, # No naf filter
            self.rome,
            self.location.latitude,
            self.location.longitude,
            self.distance,
            aggregate_by=["naf"], # Only naf aggregate
            flag_alternance=self.flag_alternance,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            departments=self.departments,
        )
        return aggregations['naf']

    def get_headcount_aggregations(self):
        _, _, aggregations = fetch_companies(
            self.naf_codes,
            self.rome,
            self.location.latitude,
            self.location.longitude,
            self.distance,
            aggregate_by=["headcount"], # Only headcount aggregate
            flag_alternance=self.flag_alternance,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=settings.HEADCOUNT_WHATEVER, # No headcount filter
            departments=self.departments,
        )
        return aggregations['headcount']

    def get_contract_aggregations(self):
        _, _, aggregations = fetch_companies(
            self.naf_codes,
            self.rome,
            self.location.latitude,
            self.location.longitude,
            self.distance,
            aggregate_by=['flag_alternance'], # Only flag_alternance aggregate
            flag_alternance=None, # No flag_alternance filter
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            departments=self.departments,
        )
        return aggregations['contract']


    def get_distance_aggregations(self):
        _, _, aggregations = fetch_companies(
            self.naf_codes,
            self.rome,
            self.location.latitude,
            self.location.longitude,
            DISTANCE_FILTER_MAX, # France
            aggregate_by=["distance"],
            flag_alternance=self.flag_alternance,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount=self.headcount,
            departments=self.departments,
        )
        return aggregations['distance']


    def get_companies(self, add_suggestions=False):

        self.company_count = self._get_company_count(self.rome, self.distance)
        logger.debug("set company_count to %s from fetch_companies", self.company_count)

        if self.from_number < 1:
            self.from_number = 1
            self.to_number = 10
        if (self.from_number - 1) % 10:
            self.from_number = 1
            self.to_number = 10
        if self.to_number > self.company_count + 1:
            self.to_number = self.company_count + 1
        if self.to_number < self.from_number:
            # this happens if a page out of bound is requested
            self.from_number = 1
            self.to_number = 10
        if self.to_number - self.from_number > settings.PAGINATION_COMPANIES_PER_PAGE:
            self.from_number = 1
            self.to_number = 10

        result = []
        aggregations = []
        if self.company_count:
            result, _, aggregations = fetch_companies(
                self.naf_codes,
                self.rome,
                self.location.latitude,
                self.location.longitude,
                self.distance,
                from_number=self.from_number,
                to_number=self.to_number,
                flag_alternance=self.flag_alternance,
                flag_junior=self.flag_junior,
                flag_senior=self.flag_senior,
                flag_handicap=self.flag_handicap,
                headcount=self.headcount,
                sort=self.sort,
                departments=self.departments,
                aggregate_by=self.aggregate_by,
            )

        if self.company_count < 10 and add_suggestions:

            # Suggest other jobs.
            alternative_rome_codes = ROME_MOBILITIES[self.rome]
            for rome in alternative_rome_codes:
                if not rome == self.rome:
                    company_count = self._get_company_count(rome, self.distance)
                    self.alternative_rome_codes[rome] = company_count

            # Suggest other distances.
            last_count = 0
            for distance, distance_label in [(30, u'30 km'), (50, u'50 km'), (3000, u'France entière')]:
                company_count = self._get_company_count(self.rome, distance)
                if company_count > last_count:
                    last_count = company_count
                    self.alternative_distances[distance] = (distance_label, last_count)

        return result, aggregations


def count_companies(naf_codes, rome_code, latitude, longitude, distance, **kwargs):
    json_body = build_json_body_elastic_search(naf_codes, rome_code, latitude, longitude, distance, **kwargs)
    del json_body["sort"]
    return count_companies_from_es(json_body)

def count_companies_from_es(json_body):
    es = Elasticsearch()
    res = es.count(index=settings.ES_INDEX, doc_type="office", body=json_body)
    return res["count"]

def fetch_companies(naf_codes, rome_code, latitude, longitude, distance, aggregate_by=None, **kwargs):
    json_body = build_json_body_elastic_search(
        naf_codes,
        rome_code,
        latitude,
        longitude,
        distance,
        aggregate_by=aggregate_by,
        **kwargs
    )

    try:
        sort = kwargs['sort']
    except KeyError:
        sort = sorting.SORT_FILTER_DEFAULT

    companies, companies_count, aggregations_raw = get_companies_from_es_and_db(json_body, sort=sort)
    companies = shuffle_companies(companies, sort, rome_code)

    # Extract aggregations
    aggregations = {}
    if aggregate_by:
        if "naf" in aggregate_by:
            aggregations['naf'] = aggregate_naf(aggregations_raw)
        if "flag_alternance" in aggregate_by:
            aggregations['contract'] = aggregate_contract(aggregations_raw)
        if 'headcount' in aggregate_by:
            aggregations['headcount'] = aggregate_headcount(aggregations_raw)
        if 'distance' in aggregate_by:
            if distance == DISTANCE_FILTER_MAX:
                aggregations['distance'] = aggregate_distance(aggregations_raw)

    return companies, companies_count, aggregations

def aggregate_naf(aggregations_raw):
    return [{
            "code": naf_aggregate['key'],
            "count": naf_aggregate['doc_count'],
            'label': settings.NAF_CODES.get(naf_aggregate['key']),
        } for naf_aggregate in aggregations_raw['naf']['buckets']]

def aggregate_contract(aggregations_raw):
    alternance_key = 1
    alternance = 0
    total = 0

    for contract_aggregate in aggregations_raw["flag_alternance"]["buckets"]:
        # key=1 means flag_alternance
        if contract_aggregate['key'] == alternance_key:
            alternance = contract_aggregate['doc_count']
        # All contracts
        total += contract_aggregate['doc_count']

    return {'alternance': alternance, 'all': total}


def aggregate_headcount(aggregations_raw):
    small = 0
    big = 0

    # Count by HEADCOUNT_INSEE values
    for contract_aggregate in aggregations_raw["headcount"]["buckets"]:
        key = contract_aggregate['key']
        if  key <= settings.HEADCOUNT_SMALL_ONLY_MAXIMUM:
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
            e.message = "Unknown distance_aggretions key : %s" % distance_aggregate['key']
            logger.exception(e)
            continue

        distances_aggregations[label] = distance_aggregate['doc_count']

    return distances_aggregations

def shuffle_companies(companies, sort, rome_code):
    """
    Slightly shuffle the results of a company search this way:
    1) in case of sort by score
    - split results in groups of companies having the exact same stars (e.g. 2.3 or 4.9)
    - shuffle each of these groups in a predictable reproductible way
    Note that the scores are adjusted to the contextual rome_code.
    2) in case of sort by distance
    same things as 1), grouping instead companies having the same distance in km.
    """
    buckets = collections.OrderedDict()
    for company in companies:
        if sort == sorting.SORT_FILTER_DISTANCE:
            key = company.distance
        elif sort == sorting.SORT_FILTER_SCORE:
            if hasattr(company, 'scores_by_rome') and company.scores_by_rome.get(rome_code) == 100:
                # make an exception for offices which were manually boosted (score for rome = 100)
                # to ensure they consistently appear on top of results
                # and are not shuffled with other offices having 5.0 stars,
                # but only score 99 and not 100
                key = 100  # special value designed to be distinct from 5.0 stars
            else:
                key = company.get_stars_for_rome_code(rome_code)
        else:
            raise ValueError("unknown sorting")
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(company)

    # generating now predictable yet divergent seed for shuffle
    # the list of results should be noticeably different from one day to the other,
    # but stay the same for a given day
    day_of_year = datetime.now().timetuple().tm_yday
    shuffle_seed = day_of_year / 366.0

    for _, bucket in buckets.iteritems():
        random.shuffle(bucket, lambda: shuffle_seed)
    companies = list(itertools.chain.from_iterable(buckets.values()))

    return companies


def build_json_body_elastic_search(
        naf_codes,
        rome_code,
        latitude,
        longitude,
        distance,
        from_number=None,
        to_number=None,
        headcount=settings.HEADCOUNT_WHATEVER,
        sort=sorting.SORT_FILTER_DEFAULT,
        flag_alternance=0,
        flag_junior=0,
        flag_senior=0,
        flag_handicap=0,
        aggregate_by=None,
        departments=None,
    ):

    score_for_rome_field_name = "scores_by_rome.%s" % rome_code

    sort_attrs = []

    # Build filters.
    filters = []
    if naf_codes:
        filters = [{
            "terms": {
                "naf": naf_codes
            }
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
        filters.append({
            "numeric_range": {
                "headcount": headcount
            }
        })

    if flag_alternance == 1:
        filters.append({
            "term": {
                "flag_alternance": 1
            }
        })

    if flag_junior == 1:
        filters.append({
            "term": {
                "flag_junior": 1
            }
        })

    if flag_senior == 1:
        filters.append({
            "term": {
                "flag_senior": 1
            }
        })

    if flag_handicap == 1:
        filters.append({
            "term": {
                "flag_handicap": 1
            }
        })

    filters.append({
        "exists": {
            "field": score_for_rome_field_name
        }
    })

    filters.append({
        "geo_distance": {
            "distance": "%skm" % distance,
            "locations": {
                "lat": latitude,
                "lon": longitude
            }
        }
    })


    if departments:
        filters.append({
            'terms': {
                'department': departments
            }
        })

    # Build sort.

    if sort not in sorting.SORT_FILTERS:
        logger.info('unknown sort: %s', sort)
        sort = sorting.SORT_FILTER_DEFAULT

    distance_sort = {
        "_geo_distance": {
            "locations": {
                "lat": latitude,
                "lon": longitude
            },
            "order": "asc",
            "unit": "km"
        }
    }

    score_sort = {
        score_for_rome_field_name: {
            "order": "desc",
            "ignore_unmapped": True,
        }
    }

    if sort == sorting.SORT_FILTER_DISTANCE:
        sort_attrs.append(distance_sort)
        sort_attrs.append(score_sort)
    elif sort == sorting.SORT_FILTER_SCORE:
        sort_attrs.append(score_sort)
        sort_attrs.append(distance_sort)

    json_body = {
        "sort": sort_attrs,
        "query": {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": filters
                    }
                }
            }
        }
    }

    # Add aggregate
    if aggregate_by:

        json_body['aggs'] = {}
        for aggregate in aggregate_by:
            # Distance if not an ES field, so we have to do a specefic aggregations
            if aggregate == 'distance':
                json_body['aggs']['distance'] = {
                    'geo_distance' : {
                        "field": "locations",
                        "origin": "%s,%s"  % (latitude, longitude),
                        'unit': 'km',
                        'ranges': [{'to': 10}, {'to': 30}, {'to': 50}, {'to': 100}, {'to': 3000}]
                    }
                }
            else:
                json_body['aggs'][aggregate] = {
                    "terms" : {
                        "field": aggregate
                    }
                }


    if from_number:
        json_body["from"] = from_number - 1
        if to_number:
            if to_number < from_number:
                # this should never happen
                logger.exception("to_number < from_number : %s < %s", to_number, from_number)
                raise Exception("to_number < from_number")
            json_body["size"] = to_number - from_number + 1

    return json_body


def get_companies_from_es_and_db(json_body, sort):
    """
    Fetch companies first from Elasticsearch, then from the database.

    Returns a tuple of (companies, companies_count), where `companies` is a
    list of results as Office instances (with some extra attributes only available
    in Elasticsearch) and `companies_count` an integer of the results number.
    """
    es = Elasticsearch()
    res = es.search(index=settings.ES_INDEX, doc_type="office", body=json_body)
    logger.info("Elastic Search request : %s", json_body)

    companies = []
    siret_list = [office["_source"]["siret"] for office in res['hits']['hits']]

    if siret_list:

        if sort == sorting.SORT_FILTER_DISTANCE:
            distance_sort_index = 0
        else:
            distance_sort_index = 1

        company_objects = Office.query.filter(Office.siret.in_(siret_list))
        company_dict = {}

        es_companies_by_siret = {
            item['_source']['siret']: item for item in res['hits']['hits']
        }

        # FIXME it's not great to add new properties to an existing object. It
        # would be better to wrap the office objects in a new OfficeResult
        # class that would add new properties related to the query.
        for obj in company_objects:
            # Get the corresponding item from the Elasticsearch results.
            es_company = es_companies_by_siret[obj.siret]
            # Add an extra `distance` attribute.
            obj.distance = int(round(es_company["sort"][distance_sort_index]))
            # Add an extra `scores_by_rome` attribute: this will allow us to identify boosted offices
            # in the search result HTML template.
            try:
                obj.scores_by_rome = es_company["_source"]["scores_by_rome"]
            except KeyError:
                obj.scores_by_rome = {}
            company_dict[obj.siret] = obj

        for siret in siret_list:
            try:
                company = company_dict[siret]
            except KeyError as e:
                e.message = "ES and DB out of sync: siret %s is in ES but not in DB - this should never happen" % siret
                logger.exception(e)
                raise
            if company.has_city():
                companies.append(company)
            else:
                logging.info("company siret %s does not have city, ignoring...", siret)

    companies_count = res['hits']['total']

    try:
        aggregations = res['aggregations']
    except KeyError:
        aggregations = []

    return companies, companies_count, aggregations


def build_location_suggestions(term):
    term = term.title()
    es = Elasticsearch()
    zipcode_match = [{
        "prefix": {
            "zipcode": term
        }
    }, ]

    city_match = [{
        "match": {
            "city_name.autocomplete": {
                "query": term
            }
        }}, {
        "match": {
            "city_name.stemmed": {
                "query": term,
                "boost": 1
            }
        }}, {
        "match_phrase_prefix": {
            "city_name.stemmed": {
                "query": term
            }
        }}]

    filters = zipcode_match

    try:
        int(term)
    except ValueError:
        filters.extend(city_match)

    body = {
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "should": filters
                    },
                },
                "field_value_factor": {
                    "field": "population",
                    "modifier": "log1p"
                }
            },
        },
        "size": 10
    }
    # FIXME ugly : in tests we use dev ES index instead of test ES index
    # we should use index=settings.ES_INDEX instead of index='labonneboite'
    # however we cannot yet since location+ogr data is not yet in ES test index data
    res = es.search(index='labonneboite', doc_type="location", body=body)

    suggestions = []
    first_score = None

    for hit in res['hits']['hits']:
        if not first_score:
            first_score = hit['_score']
        source = hit['_source']
        if source['zipcode']:  # and hit['_score'] > 0.1 * first_score:
            city_name = source['city_name'].replace('"', '')
            label = u'%s (%s)' % (city_name, source['zipcode'])
            city = {
                'city': source['slug'],
                'zipcode': source['zipcode'],
                'label': label,
                'latitude': source['location']['lat'],
                'longitude': source['location']['lon']
            }
            suggestions.append(city)
    return suggestions


def build_job_label_suggestions(term):

    es = Elasticsearch()

    body = {
        "_source": ["ogr_description", "rome_description", "rome_code"],
        "query": {
            "match": {
                # Query for multiple words or multiple parts of words across multiple fields.
                # Based on https://qbox.io/blog/an-introduction-to-ngrams-in-elasticsearch
                "_all": unidecode.unidecode(term)
            }
        },
        "aggs":{
            "by_rome_code": {
                "terms": {
                    "field": "rome_code",
                    "size": 0,
                    # Note: a maximum of 550 buckets will be fetched, as we have 550 unique ROME codes

                    # TOFIX: `order` cannot work without a computed `max_score`, see the `max_score` comment below.
                    # Order results by sub-aggregation named 'max_score'
                    # "order": {"max_score": "desc"},
                },
                "aggs": {
                    # Only 1 result per rome code: include only 1 top hit on each bucket in the results.
                    "by_top_hit": {"top_hits": {"size": 1}},

                    # TOFIX: `max_score` below does not work with Elasticsearch 1.7.
                    # Fixed in elasticsearch 2.0+:
                    # https://github.com/elastic/elasticsearch/issues/10091#issuecomment-193676966

                    # Count of the max score of any member of this bucket
                    # "max_score": {"max": {"lang": "expression", "script": "_score"}},
                },
            },
        },
        "size": 0,
    }

    # FIXME ugly : in tests we use dev ES index instead of test ES index
    # we should use index=settings.ES_INDEX instead of index='labonneboite'
    # however we cannot yet since location+ogr data is not yet in ES test index data
    res = es.search(index='labonneboite', doc_type="ogr", body=body)

    suggestions = []

    # Since ordering cannot be done easily through Elasticsearch 1.7 (`max_score` not working),
    # we do it in Python at this time.
    results = res[u'aggregations'][u'by_rome_code'][u'buckets']
    results.sort(key=lambda e: e['by_top_hit']['hits']['max_score'], reverse=True)

    for hit in results:
        if len(suggestions) < settings.AUTOCOMPLETE_MAX:
            hit = hit[u'by_top_hit'][u'hits'][u'hits'][0]
            source = hit['_source']
            highlight = hit.get('highlight', {})
            try:
                rome_description = highlight['rome_description.autocomplete'][0]
            except KeyError:
                rome_description = source['rome_description']
            try:
                ogr_description = highlight['ogr_description.autocomplete'][0]
            except KeyError:
                ogr_description = source['ogr_description']
            label = "%s (%s, ...)" % (rome_description, ogr_description)
            value = "%s (%s, ...)" % (source["rome_description"], source["ogr_description"])
            suggestions.append({
                'id': source['rome_code'],
                'label': label,
                'value': value,
                'occupation': slugify(source['rome_description'].lower()),
            })
        else:
            break

    return suggestions
