import csv
import logging
import os
import urllib

import requests

logger = logging.getLogger('main')


COORDINATES_CACHE = {}
COMMUNES_CACHE = {}


# --------- BEGIN INTERNAL FUNCTIONS

def load_names_and_coordinates_for_zipcodes():
    names_and_coordinates_by_zipcode = {}
    fullname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "zipcode_geocoding.csv")
    with open(fullname, 'r') as city_file:
        reader = csv.reader(city_file)
        for fields in reader:
            zipcode = fields[1]
            latitude = fields[2]
            longitude = fields[3]
            name = fields[0]
            names_and_coordinates_by_zipcode[zipcode] = (name, latitude, longitude)
    return names_and_coordinates_by_zipcode


def zipcode_is_arrondissement(zipcode):
    start_zipcodes = ['13', '69', '75']
    for start in start_zipcodes:
        if zipcode.startswith(start):
            if zipcode in [str((int(start) * 1000 + i)) for i in range(0, 21)]:
                return True
    return False


def load_coordinates_for_cities():
    city_coordinates = []
    fullname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/villes_france.csv")
    with open(fullname, 'r') as city_file:
        reader = csv.reader(city_file)
        names_and_coordinates_by_zipcode = load_names_and_coordinates_for_zipcodes()
        for fields in reader:
            zipcode = fields[8]
            # city_slug = fields[2]
            city_name = fields[5]
            latitude = fields[20]
            longitude = fields[19]
            population = int(fields[14])
            if "-" in zipcode:
                first_zipcode = zipcode.split("-")[0]
                if zipcode_is_arrondissement(first_zipcode):
                    zipcodes = zipcode.split("-")
                    for zipcode in zipcodes:
                        try:
                            city_name, latitude, longitude = names_and_coordinates_by_zipcode[zipcode]
                            city_coordinates.append((None, city_name, zipcode, population, latitude, longitude))
                        except KeyError:
                            logger.info(
                                'warning : zipcode %s present in villes_france.csv but absent '
                                'in zipcode_geocoding.csv' % zipcode)
                else:
                    city_coordinates.append((None, city_name, first_zipcode, population, latitude, longitude))
            else:
                city_coordinates.append((None, city_name, zipcode, population, latitude, longitude))
    return city_coordinates


# -------- END INTERNAL FUNCTIONS


def get_city_name_and_zipcode_from_commune_id(commune):
    """
    # Zipcodes versus Commune ids

    Even if they may look similar, these two code systems are strictly different and not to be mixed up:

    - Commune ids (`commune_id` in the code, aka "code INSEE" in French)
    - Zipcodes (`zipcode` in the code, aka "code postal" or "CP" in French)

    Examples:

    - 57000 (departement of Metz) is a zipcode and not a commune id, the corresponding commune_id is 57463.
    - 14118 (Caen) is a commune id and not a zipcode, but its corresponding zipcode is 14000.
    """
    if not COMMUNES_CACHE:
        fullname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/villes_france.csv")
        with open(fullname, 'r') as city_file:
            reader = csv.reader(city_file)
            for line in reader:
                # a city might have several "communes" (ex. Paris ? in our file, there is only one commune ID for a city,
                # but seems wrong by INSEE standards). For now, go with the one commune id we have here.
                commune_id = line[10]
                city_slug = line[2]
                zipcode = line[8]
                # if there are several zipcodes for a city, we just take the first one for now... ex. Paris --> 75001
                if "-" in zipcode:
                    zipcode = zipcode.split("-")[0]
                COMMUNES_CACHE[commune_id] = (city_slug, zipcode)

    if commune in COMMUNES_CACHE:
        return COMMUNES_CACHE[commune]
    return None, None


def load_coordinates():
    if not COORDINATES_CACHE:
        logger.info("loading coordinates from file consolidated_cities.csv")
        fullname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/consolidated_cities.csv")
        with open(fullname, 'r') as city_file:
            reader = csv.reader(city_file)
            for city_name, first_zipcode, population, latitude, longitude in reader:
                COORDINATES_CACHE[first_zipcode] = (latitude, longitude)
        logger.info("enriching coordinates from file villes_france.csv")
        coordinates = load_coordinates_for_cities()
        for c in coordinates:
            zipcode = c[2]
            latitude = c[4]
            longitude = c[5]
            if zipcode not in COORDINATES_CACHE:
                COORDINATES_CACHE[zipcode] = (latitude, longitude)

    return COORDINATES_CACHE


def get_lat_long_from_zipcode(zipcode):
    """
    Returns a tuple of the (latitude, longitude) for the given zipcode.
    """
    coordinates = load_coordinates()
    if zipcode in coordinates:
        return coordinates[zipcode]
    return None, None


def get_all_lat_long_from_departement(departement):
    """
    Returns a list of tuple of the (latitude, longitude) of all zipcodes for the given departement.
    """
    coordinates = load_coordinates()
    return [lat_long for zipcode, lat_long in coordinates.items() if zipcode.startswith(departement)]
