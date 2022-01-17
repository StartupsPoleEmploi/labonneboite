from functools import lru_cache
from slugify import slugify
from text_unidecode import unidecode
from labonneboite.common.es import Elasticsearch
from labonneboite.conf import settings

MAX_JOBS = 10
MAX_LOCATIONS = 10

# This file is a fallback which uses ES, we normally use the "address API" from beta.gouv.fr

@lru_cache(maxsize=8 * 1024)
def build_location_suggestions(term):
    if term.strip() == '':
        return []
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
                "query": term,
            }
        }}, {
        "match": {
            "city_name.stemmed": {
                "query": term,
                "boost": 1,
            }
        }}, {
        "match_phrase_prefix": {
            "city_name.stemmed": {
                "query": term,
            }
        }}]

    filters = zipcode_match

    try:
        int(term)
    except ValueError:
        filters.extend(city_match)

    body = {
        "query": {
            # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html
            "function_score": {
                "query": {
                    "bool": {
                        "should": filters,
                    },
                },
                # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html#function-field-value-factor
                "field_value_factor": {
                    "field": "population",
                    "modifier": "log1p",
                }
            },
        },
        "size": MAX_LOCATIONS,
    }
    res = es.search(index=settings.ES_INDEX, doc_type="location", body=body)

    suggestions = []
    first_score = None

    for hit in res['hits']['hits']:
        if not first_score:
            first_score = hit['_score']
        source = hit['_source']
        if source['zipcode']:  # and hit['_score'] > 0.1 * first_score:
            city_name = source['city_name'].replace('"', '')
            label = '%s (%s)' % (city_name, source['zipcode'])
            city = {
                'city': source['slug'],
                'zipcode': source['zipcode'],
                'label': label,
                'latitude': source['location']['lat'],
                'longitude': source['location']['lon'],
            }
            suggestions.append(city)
    return suggestions


def enrich_job_term_with_thesaurus(term):
    """
    This thesaurus is an attempt at improving job autocompletion quality
    for specific keywords which give poor results otherwise.
    For example "ios" would match "Vendeur en kiosque".
    """
    thesaurus = {
        'ios': 'informatique',
        'android': 'informatique',
    }
    words = term.split(' ')
    for idx, word in enumerate(words):
        if word.lower() in thesaurus:
            words[idx] = thesaurus[word.lower()]
    term = ' '.join(words)
    return term


@lru_cache(maxsize=8 * 1024)
def build_job_label_suggestions(term, size=MAX_JOBS):
    term = enrich_job_term_with_thesaurus(term)

    es = Elasticsearch()

    body = {
        "_source": ["ogr_description", "rome_description", "rome_code"],
        "query": {
            "match": {
                # Query for multiple words or multiple parts of words across multiple fields.
                # Based on https://qbox.io/blog/an-introduction-to-ngrams-in-elasticsearch
                "_all": unidecode.unidecode(term),
            }
        },
        "aggs": {
            "by_rome_code": {
                "terms": {
                    "field": "rome_code",
                    "size": 0,
                    # Note: a maximum of 550 buckets will be fetched, as we have 550 unique ROME codes

                    # FIXME `order` cannot work without a computed `max_score`, see the `max_score` comment below.
                    # Order results by sub-aggregation named 'max_score'
                    # "order": {"max_score": "desc"},
                },
                "aggs": {
                    # Only 1 result per rome code: include only 1 top hit on each bucket in the results.
                    # Another way of saying this is that for all OGR matching a given ROME, we only
                    # keep the most relevant OGR.
                    "by_top_hit": {"top_hits": {"size": 1}},

                    # FIXME `max_score` below does not work with Elasticsearch 1.7.
                    # Fixed in elasticsearch 2.0+:
                    # https://github.com/elastic/elasticsearch/issues/10091#issuecomment-193676966

                    # FTR @vermeer made another try to find a workaround as of Feb 2018, and failed.
                    # The only way out is to upgrade to elasticsearch 2.0+

                    # Set max score among all members of this bucket
                    # "max_score": {"max": {"lang": "expression", "script": "_score"}},
                },
            },
        },
        "size": 0,
    }

    res = es.search(index=settings.ES_INDEX, doc_type="ogr", body=body)

    suggestions = []

    # Since ordering cannot be done easily through Elasticsearch 1.7 (`max_score` not working),
    # we do it in Python at this time.
    results = res['aggregations']['by_rome_code']['buckets']
    results.sort(key=lambda e: e['by_top_hit']['hits']['max_score'], reverse=True)

    for hit in results:
        if len(suggestions) < size:
            hit = hit['by_top_hit']['hits']['hits'][0]
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
            score = round(hit['_score'], 1)
            suggestions.append({
                'id': source['rome_code'],
                'label': label,
                'value': value,
                'occupation': slugify(source['rome_description'].lower()),
                'score': score,
            })
        else:
            break

    return suggestions


