"""
Etablissements are imported for Pole Emploi databases without geo coordinates.

This module assists in finding and assigning geo coordinates to etablissements.

Documentation about the open data API we use here:
https://adresse.data.gouv.fr/api/
https://adresse.data.gouv.fr/faq/
"""
import requests
import gevent
from gevent.pool import Pool
import gevent.monkey
from sqlalchemy.exc import IntegrityError

from labonneboite.common.database import db_session
from labonneboite.common.load_data import load_city_codes
from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.common.util import timeit
from labonneboite.importer.models.computing import Geolocation
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger

gevent.monkey.patch_socket()

# maximum 10 requests in parrallel, as can be seen on
# https://adresse.data.gouv.fr/faq/
pool_size = 10
connection_limit = pool_size
adapter = requests.adapters.HTTPAdapter(pool_connections=connection_limit,
                                        pool_maxsize=connection_limit,
                                        max_retries=4)
session = requests.session()
session.mount('http://', adapter)
jobs = []
pool = Pool(pool_size)

CITY_NAMES = load_city_codes()
GEOCODING_STATS = {}


class IncorrectAdressDataException(Exception):
    pass


class AbnormallyLowGeocodingRatioException(Exception):
    pass


class GeocodeJob(Job):

    def get_full_adress(self, street_number, street_name, zipcode, city):
        if "arrondissement" in city.lower():
            city = city.split(" ")[0]
            if city.lower() not in ["paris", "lyon", "marseille"]:
                raise IncorrectAdressDataException

        if "LIEU DIT " in street_name:
            street_name = street_name.replace("LIEU DIT ", "")
            street_number = ""

        full_address = "%s %s %s %s" % (street_number, street_name, zipcode, city)
        return full_address.strip()

    @timeit
    def create_geocoding_jobs(self):
        query = """
            select
                siret,
                numerorue,
                libellerue,
                codepostal,
                codecommune,
                coordinates_x,
                coordinates_y
            from %s
        """ % (settings.SCORE_REDUCING_TARGET_TABLE)
        _, cur = import_util.create_cursor()
        cur.execute(query)
        rows = cur.fetchall()
        geocoding_jobs = []
        count = 0
        for row in rows:
            siret, street_number, street_name, zipcode, codecommune, coordinates_x, coordinates_y = row
            try:
                city = CITY_NAMES[codecommune]
            except KeyError:
                logger.warning("wrong codecommune: %s", codecommune)
                continue
            try:
                full_address = self.get_full_adress(street_number, street_name, zipcode, city)
                initial_coordinates = [coordinates_x, coordinates_y]
                geocoding_jobs.append([siret, full_address, initial_coordinates])
            except IncorrectAdressDataException:
                logger.warning("incorrect address for %s %s %s %s", street_number, street_name, zipcode, city)
            count += 1
            GEOCODING_STATS['jobs'] = GEOCODING_STATS.get('jobs', 0) + 1
            if not count % 10000:
                logger.info("loading geocoding jobs from db... loaded %s rows", count)
        logger.info("%i geocoding jobs created...", len(geocoding_jobs))
        return geocoding_jobs


    @timeit
    def update_coordinates(self, coordinates_updates):
        con, cur = import_util.create_cursor()
        count = 0
        statements = []
        update_query = "update %s set coordinates_x=%%s, coordinates_y=%%s where siret=%%s" % \
            settings.SCORE_REDUCING_TARGET_TABLE

        for siret, coordinates in coordinates_updates:
            count += 1
            statements.append([coordinates[0], coordinates[1], siret])
            if len(statements) == 1000:
                logger.info("geocoding with ban... %i of %i done", count, len(coordinates_updates))
                cur.executemany(update_query, statements)
                con.commit()
                statements = []

        if len(statements) >= 1:
            logger.info("geocoding with ban... %i of %i done", count, len(coordinates_updates))
            cur.executemany(update_query, statements)
            con.commit()   
            

    @timeit
    def validate_coordinates(self):
        _, cur = import_util.create_cursor()
        query = """
        select
        sum(
            (coordinates_x > 0 or coordinates_x < 0)
            and
            (coordinates_y > 0 or coordinates_y < 0)
        )/count(*)
        from %s
        """ % settings.SCORE_REDUCING_TARGET_TABLE
        cur.execute(query)
        geocoding_ratio = cur.fetchall()[0][0]
        logger.info("geocoding_ratio = %s", geocoding_ratio)
        if geocoding_ratio < settings.MINIMUM_GEOCODING_RATIO:
            raise AbnormallyLowGeocodingRatioException


    @timeit
    def run_geocoding_jobs(self, geocoding_jobs):
        ban_jobs = []
        coordinates_updates = []
        count = 0
        for siret, full_address, initial_coordinates in geocoding_jobs:
            unit = GeocodeUnit(siret, full_address, coordinates_updates, initial_coordinates)
            job_id = pool.spawn(unit.find_coordinates_for_address)
            ban_jobs.append(job_id)
            count += 1
            if not count % 1000:
                logger.info("running geocoding jobs : started %s of %s jobs, collected %s coordinates so far",
                        count,
                        len(geocoding_jobs),
                        len(coordinates_updates),
                        )
                gevent.joinall(ban_jobs)
                ban_jobs = []
        # processing remaining jobs
        gevent.joinall(ban_jobs)
        return coordinates_updates


    @timeit
    def run(self):
        logger.info("starting geocoding task...")
        geocoding_jobs = self.create_geocoding_jobs()
        logger.info("requesting BAN for all the adresses we need to geocode for...")
        coordinates_updates = self.run_geocoding_jobs(geocoding_jobs)
        logger.info("updating coordinates...")
        self.update_coordinates(coordinates_updates)
        logger.info("updated %i coordinates !", len(coordinates_updates))
        logger.info("GEOCODING_STATS = %s", GEOCODING_STATS)
        logger.info("validating coordinates...")
        self.validate_coordinates()
        logger.info("validated coordinates !")
        logger.info("completed geocoding task.")


class GeocodeUnit(object):

    def __init__(self, siret, address, updates, initial_coordinates):
        self.siret = siret
        self.full_address = address
        self.updates = updates
        self.initial_coordinates = initial_coordinates

    def find_coordinates_for_address(self):
        """
        finding coordinates for an address based on the BAN (base d'adresses nationale),
        an online governmental service.
        """
        coordinates = None
        BASE = "http://api-adresse.data.gouv.fr/search/?q="
        geocoding_request = "%s%s" % (BASE, self.full_address)
        geolocation = Geolocation.get(self.full_address)

        if geolocation:
            # coordinates were already queried and cached before
            coordinates = [geolocation.x, geolocation.y]
            GEOCODING_STATS['cache_hits'] = GEOCODING_STATS.get('cache_hits', 0) + 1
        else:
            # coordinates need to be queried and cached
            response = session.get(geocoding_request)
            response.close()
            GEOCODING_STATS['cache_misses'] = GEOCODING_STATS.get('cache_misses', 0) + 1
            if response.status_code == 200:
                try:
                    results = response.json()['features']
                    if len(results) >= 1:
                        coordinates = results[0][u'geometry'][u'coordinates']
                        # let's cache the result for later computations
                        geolocation = Geolocation(
                            full_address=self.full_address,
                            x=coordinates[0],
                            y=coordinates[1]
                            )
                        db_session.add(geolocation)

                        # as this method is run in parallel jobs,
                        # let's commit often so that each job see each other's changes
                        # and rollback in case of rare simultaneous changes on same geolocation
                        try:
                            db_session.commit()
                            # usually flush() is called as part of commit()
                            # however it is not the case in our project
                            # because autoflush=False
                            db_session.flush()
                            GEOCODING_STATS['flushes'] = GEOCODING_STATS.get('flushes', 0) + 1
                        except IntegrityError:
                            # happens when a job tries to insert an already existing full_address
                            # rollback needed otherwise db_session is left
                            # in a state unusable by the other parallel jobs
                            db_session.rollback()
                            GEOCODING_STATS['rollbacks'] = GEOCODING_STATS.get('rollbacks', 0) + 1
                except ValueError:
                    logger.warn('ValueError in json-ing features result %s', response.text)

        if coordinates:
            if coordinates == self.initial_coordinates:
                GEOCODING_STATS['unchanged_coordinates'] = GEOCODING_STATS.get('unchanged_coordinates', 0) + 1
            else:
                GEOCODING_STATS['updatable_coordinates'] = GEOCODING_STATS.get('updatable_coordinates', 0) + 1
                self.updates.append([self.siret, coordinates])
        else:
            GEOCODING_STATS['coordinates_not_found'] = GEOCODING_STATS.get('coordinates_not_found', 0) + 1


if __name__ == "__main__":
    geocode_task = GeocodeJob()
    geocode_task.run()
