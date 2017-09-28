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
from labonneboite.common.models import Office
from labonneboite.conf import settings


logger = logging.getLogger('main')


PUBLIC_ALL = 0
PUBLIC_JUNIOR = 1
PUBLIC_SENIOR = 2
PUBLIC_HANDICAP = 3
PUBLIC_CHOICES = [PUBLIC_ALL, PUBLIC_JUNIOR, PUBLIC_SENIOR, PUBLIC_HANDICAP]


class InvalidZipcodeError(Exception):
    pass

class Fetcher(object):

    def __init__(self, **kwargs):
        self.city_slug = kwargs.get('city')
        self.occupation_slug = kwargs.get('occupation')
        self.distance = kwargs.get('distance')
        self.sort = kwargs.get('sort')
        self.zipcode = kwargs.get('zipcode')


        # Pagination.
        self.from_number = int(kwargs.get('from') or 1)
        self.to_number = int(kwargs.get('to') or 10)

        # Flags.
        self.flag_alternance = kwargs.get('flag_alternance')
        public = kwargs.get('public')
        self.flag_handicap = public == PUBLIC_HANDICAP
        self.flag_junior = public == PUBLIC_JUNIOR
        self.flag_senior = public == PUBLIC_SENIOR

        # Headcount.
        self.headcount = kwargs.get('headcount')
        try:
            self.headcount_filter = int(self.headcount)
        except (TypeError, ValueError):
            self.headcount_filter = settings.HEADCOUNT_WHATEVER

        # NAF, ROME and NAF codes.
        self.naf = kwargs.get('naf')

        self.rome = mapping_util.SLUGIFIED_ROME_LABELS[self.occupation_slug]

        # Empty list is needed to handle companies with ROME not related to their NAF
        self.naf_codes = {}
        if self.naf:
            self.naf_codes = mapping_util.map_romes_to_nafs([self.rome], [self.naf])
        # Other properties.
        self.alternative_rome_codes = {}
        self.alternative_distances = collections.OrderedDict()
        self.company_count = None

    def init_location(self):
        # Latitude/longitude.
        city = geocoding.get_city_by_zipcode(self.zipcode, self.city_slug)
        if not city:
            logger.debug("unable to retrieve a city for zipcode `%s` and slug `%s`", self.zipcode, self.city_slug)
            raise InvalidZipcodeError
        self.latitude = city['coords']['lat']
        self.longitude = city['coords']['lon']

    def _get_company_count(self, rome_code, distance):
        return count_companies(
            self.naf_codes,
            rome_code,
            self.latitude,
            self.longitude,
            distance,
            flag_alternance=self.flag_alternance,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount_filter=self.headcount_filter,
        )

    def get_naf_aggregations(self):
        _, _, aggregations = fetch_companies(
            {}, # No naf filter
            self.rome,
            self.latitude,
            self.longitude,
            self.distance,
            flag_alternance=self.flag_alternance,
            flag_junior=self.flag_junior,
            flag_senior=self.flag_senior,
            flag_handicap=self.flag_handicap,
            headcount_filter=self.headcount_filter,
            aggregate_by="naf"
        )
        return aggregations

    def get_companies(self):

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

        result = aggregations = []
        if self.company_count:
            result, _, aggregations = fetch_companies(
                self.naf_codes,
                self.rome,
                self.latitude,
                self.longitude,
                self.distance,
                from_number=self.from_number,
                to_number=self.to_number,
                flag_alternance=self.flag_alternance,
                flag_junior=self.flag_junior,
                flag_senior=self.flag_senior,
                flag_handicap=self.flag_handicap,
                headcount_filter=self.headcount_filter,
                sort=self.sort,
                aggregate_by="naf"
            )

        if self.company_count < 10:

            # Suggest other jobs.
            alternative_rome_codes = settings.ROME_MOBILITIES[self.rome]
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
    es = Elasticsearch()
    res = es.count(index=settings.ES_INDEX, doc_type="office", body=json_body)
    return res["count"]

def fetch_companies(naf_codes, rome_code, latitude, longitude, distance, **kwargs):
    json_body = build_json_body_elastic_search(naf_codes, rome_code, latitude, longitude, distance, **kwargs)

    try:
        sort = kwargs['sort']
    except KeyError:
        sort = settings.SORT_FILTER_DEFAULT

    companies, companies_count, aggregations = get_companies_from_es_and_db(json_body, sort=sort)
    companies = shuffle_companies(companies, sort, rome_code)

    # Extract aggregation
    if aggregations:
        aggregations = aggregations[kwargs["aggregate_by"]]["buckets"]
        aggregations = [
            {"naf": naf_aggregate['key'], "count": naf_aggregate['doc_count']} for naf_aggregate in aggregations
        ]

    return companies, companies_count, aggregations


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
        if sort == settings.SORT_FILTER_DISTANCE:
            key = company.distance
        elif sort == settings.SORT_FILTER_SCORE:
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
        headcount_filter=settings.HEADCOUNT_WHATEVER,
        sort=settings.SORT_FILTER_DEFAULT,
        flag_alternance=0,
        flag_junior=0,
        flag_senior=0,
        flag_handicap=0,
        aggregate_by=None):

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
        headcount_filter = int(headcount_filter)
    except ValueError:
        headcount_filter = settings.HEADCOUNT_WHATEVER

    max_office_size = None
    min_office_size = None
    if headcount_filter == settings.HEADCOUNT_SMALL_ONLY:
        max_office_size = settings.HEADCOUNT_SMALL_ONLY_MAXIMUM
    elif headcount_filter == settings.HEADCOUNT_BIG_ONLY:
        min_office_size = settings.HEADCOUNT_BIG_ONLY_MINIMUM

    if min_office_size or max_office_size:
        if min_office_size:
            headcount_filter = {"gte": min_office_size}
        if max_office_size:
            headcount_filter = {"lte": max_office_size}
        filters.append({
            "numeric_range": {
                "headcount": headcount_filter
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

    # Build sort.

    if sort not in settings.SORT_FILTERS:
        logger.info('unknown sort: %s', sort)
        sort = settings.SORT_FILTER_DEFAULT

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

    if sort == settings.SORT_FILTER_DISTANCE:
        sort_attrs.append(distance_sort)
        sort_attrs.append(score_sort)
    elif sort == settings.SORT_FILTER_SCORE:
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
        json_body['aggs'][aggregate_by] = {
            "terms" : {
                "field": aggregate_by
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

        if sort == settings.SORT_FILTER_DISTANCE:
            distance_sort_index = 0
        else:
            distance_sort_index = 1

        company_objects = Office.query.filter(Office.siret.in_(siret_list))
        company_dict = {}

        for obj in company_objects:
            # Get the corresponding item from the Elasticsearch results.
            es_company = next((item for item in res['hits']['hits'] if item["_source"]["siret"] == obj.siret))
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
            company = company_dict[siret]
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
