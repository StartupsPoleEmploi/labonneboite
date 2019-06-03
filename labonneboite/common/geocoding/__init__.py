# coding: utf8
from functools import wraps
import collections
import json
import os
import geopy.distance

from slugify import slugify

from labonneboite.common import departements
from labonneboite.common.util import unique_elements
from . import datagouv


CACHE = {}


def city_as_dict(item):
    first_zipcode = item['codesPostaux'][0]

    # Use the "main" zipcode for cities that are subdivided into arrondissements.
    if item['nom'] == 'Lyon':
        first_zipcode = "69000"
    elif item['nom'] == 'Marseille':
        first_zipcode = "13000"
    elif item['nom'] == 'Paris':
        first_zipcode = "75000"

    return {
        'name': item['nom'],
        'slug': slugify(item['nom']),
        'commune_id': item['code'],
        'zipcodes': item['codesPostaux'],
        'zipcode': first_zipcode,
        'population': item['population'],
        'coords': {
            'lon': item['centre']['coordinates'][0],
            'lat': item['centre']['coordinates'][1],
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
        "17004",  # Île-d'Aix (Fort-Boyard)
        # Communes without `population` attribute.
        # ----------------------------------------
        # Meuse (starting with 55), because there is no more inhabitants.
        "55039", "55050", "55139", "55189", "55239", "55307",
        # Mayotte (starting with 976), because there is no accurate population data available yet.
        "97601", "97602", "97603", "97604", "97605", "97606", "97607", "97608", "97609",
        "97610", "97611", "97612", "97613", "97614", "97615", "97616", "97617",
    ]

    cities = []

    json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/cities.json")
    with open(json_file, 'r') as json_data:
        for item in json.load(json_data):
            if item['code'] not in COMMUNES_TO_SKIP:
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
        for commune_id, city in list(CACHE['cities_by_commune_id'].items())
        if commune_id.startswith(departement)
    ]


@cities_cache_required
def get_distance_between_commune_id_and_coordinates(commune_id, latitude, longitude):
    """
    Return distance (float, kilometers) from commune_id to gps coordinates
    """
    city = get_city_by_commune_id(commune_id)
    coords_1 = (city['coords']['lat'], city['coords']['lon'])
    coords_2 = (latitude, longitude)
    return geopy.distance.geodesic(coords_1, coords_2).km


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
    if not address:
        return []

    features = []
    for result in datagouv.search(address, limit=limit):
        try:
            feature = {
                'latitude': result['geometry']['coordinates'][1],
                'longitude': result['geometry']['coordinates'][0],
                'label': result['properties']['label'],
                'zipcode': result['properties']['postcode'],
                'city': result['properties']['city']
            }
            # The zipcode is normally always present in the label,
            # but sometimes is inconsistently absent from it (e.g. Saint-Paul)
            # thus we add it if necessary.
            if feature['zipcode'] not in feature['label']:
                feature['label'] += " %s" % feature['zipcode']
            features.append(feature)
        except KeyError:
            continue

    return unique_elements(features, key=lambda x: (x['latitude'], x['longitude']))


def get_address(latitude, longitude, limit=10):
    """
    Returns a list of dict with keys:

        label (str)
        zipcode (str)
        city (str)
    """
    features = []
    for result in datagouv.reverse(latitude, longitude, limit=limit):
        try:
            features.append({
                'label': result['properties']['label'],
                'zipcode': result['properties']['postcode'],
                'city': result['properties']['city']
            })
        except KeyError:
            pass
    return unique_elements(features)
