# coding: utf8
from functools import wraps
import collections
import json
import os

from slugify import slugify

from labonneboite.common import departements
from labonneboite.common.util import unique_elements
from . import datagouv


CACHE = {}


def city_as_dict(item):
    first_zipcode = item[u'codesPostaux'][0]

    # Use the "main" zipcode for cities that are subdivided into arrondissements.
    if item[u'nom'] == 'Lyon':
        first_zipcode = u"69000"
    elif item[u'nom'] == 'Marseille':
        first_zipcode = u"13000"
    elif item[u'nom'] == 'Paris':
        first_zipcode = u"75000"

    return {
        'name': item[u'nom'],
        'slug': slugify(item[u'nom']),
        'commune_id': item[u'code'],
        'zipcodes': item[u'codesPostaux'],
        'zipcode': first_zipcode,
        'population': item[u'population'],
        'coords': {
            'lon': item[u'centre'][u'coordinates'][0],
            'lat': item[u'centre'][u'coordinates'][1],
        },
    }


def load_cities_cache():
    """
    Populates the cities cache with all cities in France (with their geographical coordinates and more).

    The data source is a JSON file that comes from api.gouv.fr's GeoAPI: https://docs.geo.api.gouv.fr
    The JSON file is generated with the following bash command:
        export URL="https://geo.api.gouv.fr/communes?fields=nom,code,codesPostaux,centre,population&boost=population"
        wget $URL -O cities-`date +%Y-%m-%d`.json

    However the data source does not go down to the "arrondissement" level yet.
    This feature is in the GeoAPI roadmap and planned for autumn 2017.
    Meanwhile the `cities-arrondissements.json` file is created manually with the same JSON structure.
    Population data is based on INSEE data:
    https://www.insee.fr/fr/statistiques/fichier/2525755/dep75.pdf
    https://www.insee.fr/fr/statistiques/fichier/2525755/dep13.pdf
    https://www.insee.fr/fr/statistiques/fichier/2525755/dep69.pdf
    """

    # GeoAPI known issues, waiting for a fix.
    COMMUNES_TO_SKIP = [
        # Communes without `centre` attribute.
        # ------------------------------------
        u"17004",  # Île-d'Aix (Fort-Boyard)
        # Communes without `population` attribute.
        # ----------------------------------------
        # Meuse (starting with 55), because there is no more inhabitants.
        u"55039", u"55050", u"55139", u"55189", u"55239", u"55307",
        # Mayotte (starting with 976), because there is no accurate population data available yet.
        u"97601", u"97602", u"97603", u"97604", u"97605", u"97606", u"97607", u"97608", u"97609",
        u"97610", u"97611", u"97612", u"97613", u"97614", u"97615", u"97616", u"97617",
    ]

    cities = []

    json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/cities.json")
    with open(json_file, 'r') as json_data:
        for item in json.load(json_data):
            if item[u'code'] not in COMMUNES_TO_SKIP:
                cities.append(city_as_dict(item))

    json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/arrondissements_as_cities.json")
    with open(json_file, 'r') as json_data:
        for item in json.load(json_data):
            cities.append(city_as_dict(item))

    CACHE['cities'] = cities

    # Create a dict where each "code commune (INSEE)" is mapped to its corresponding city.
    # This works because a code commune is unique for each city.
    CACHE['cities_by_commune_id'] = {city['commune_id']: city for city in cities}

    # Create a dict where each "zipcode" is mapped to its corresponding cities.
    # Since the zipcode is not unique, it can be mapped to several cities.
    CACHE['cities_by_zipcode'] = collections.defaultdict(list)
    for city in cities:
        key = city['zipcode']
        CACHE['cities_by_zipcode'][key].append(city)


def cities_cache_required(function):
    """
    A decorator that ensures that cities cache is loaded.
    """
    @wraps(function)
    def decorated(*args, **kwargs):
        if not CACHE:
            load_cities_cache()
        return function(*args, **kwargs)

    return decorated


@cities_cache_required
def get_cities():
    return CACHE['cities']


@cities_cache_required
def get_city_by_commune_id(commune_id):
    """
    Returns the city corresponding to the given commune_id string or None.
    """
    if isinstance(commune_id, int):
        commune_id = str(commune_id)
    return CACHE['cities_by_commune_id'].get(commune_id)


@cities_cache_required
def get_city_by_zipcode(zipcode, slug=''):
    """
    Returns the city corresponding to the given `zipcode` string and `city_name_slug`.
    `city_name_slug` is required to deal with situations where a zipcode is not unique for a city.
    """
    cities = CACHE['cities_by_zipcode'].get(zipcode)
    if not cities:
        return None
    if len(cities) > 1:
        for city in cities:
            if not slug or city['slug'] == slug:
                return city
    return cities[0]


@cities_cache_required
def get_all_cities_from_departement(departement):
    """
    Returns a list of all cities for the given departement.
    """
    return [
        city
        for commune_id, city in CACHE['cities_by_commune_id'].items()
        if commune_id.startswith(departement)
    ]


@cities_cache_required
def is_commune_id(value):
    """
    Returns true if the given string is a "code commune (INSEE)", false otherwise.
    """
    return value in CACHE['cities_by_commune_id']


def is_departement(value):
    """
    Returns true if the given string is a departement, false otherwise.

    Note: this requires searching in a list of 96 elements, but it's not that bad.
    """
    return value in departements.DEPARTEMENTS


def get_coordinates(address, limit=10):
    """
    Returns a list of dict with keys:

        label (str)
        latitude (float)
        longitude (float)
    """
    features = [
        {
            'latitude': result['geometry']['coordinates'][1],
            'longitude': result['geometry']['coordinates'][0],
            'label': result['properties']['label'],
        } for result in datagouv.search(address, limit=limit)
    ]

    return unique_elements(features)


def get_address(latitude, longitude, limit=10):
    """
    Returns a list of dict with keys:

        label (str)
        zipcode (str)
        city (str)
    """
    features = [
        {
            'label': result['properties']['label'],
            'zipcode': result['properties']['postcode'],
            'city': result['properties']['city']
        } for result in datagouv.reverse(latitude, longitude, limit=limit)
    ]
    return unique_elements(features)
