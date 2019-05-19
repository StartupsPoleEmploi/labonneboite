"""
Etablissements are imported for Pole Emploi databases without geo coordinates.

This module assists in finding and assigning geo coordinates to etablissements.

Documentation about the open data API we use here:
https://adresse.data.gouv.fr/api
https://adresse.data.gouv.fr/faq
"""
from multiprocessing import Manager, Pool
import io
import csv
import requests
from sqlalchemy.exc import IntegrityError
import pandas as pd
import numpy

from labonneboite.common.database import db_session
from labonneboite.common.load_data import load_city_codes
from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.common.util import timeit
from labonneboite.importer.models.computing import Geolocation
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger

# maximum 10 requests in parrallel, as can be seen on
# https://adresse.data.gouv.fr/faq/
pool_size = 8
connection_limit = pool_size
adapter = requests.adapters.HTTPAdapter(pool_connections=connection_limit,
                                        pool_maxsize=connection_limit,
                                        max_retries=4)
session = requests.session()
session.mount('http://', adapter)
jobs = []

CITY_NAMES = load_city_codes()
GEOCODING_STATS = {}

manager = Manager()
#Shared variables between processes
adresses_not_geolocated = manager.list() #list to store the geolocations not saved in cache
coordinates_updates = manager.list() #list to store the coordinates to update

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
        con, cur = import_util.create_cursor()
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
                geocoding_jobs.append([siret, full_address, initial_coordinates, codecommune])
            except IncorrectAdressDataException:
                logger.warning("incorrect address for %s %s %s %s", street_number, street_name, zipcode, city)
            count += 1
            GEOCODING_STATS['jobs'] = GEOCODING_STATS.get('jobs', 0) + 1
            if not count % 10000:
                logger.info("loading geocoding jobs from db... loaded %s rows", count)
        logger.info("%i geocoding jobs created...", len(geocoding_jobs))
        cur.close()
        con.close()
        return geocoding_jobs


    @timeit
    def update_coordinates(self, updates):
        con, cur = import_util.create_cursor()
        count = 0
        statements = []
        update_query = "update %s set coordinates_x=%%s, coordinates_y=%%s where siret=%%s" % \
            settings.SCORE_REDUCING_TARGET_TABLE

        for siret, coordinates in updates:
            count += 1
            statements.append([coordinates[0], coordinates[1], siret])
            if len(statements) == 1000:
                logger.info("geocoding with ban... %i of %i done", count, len(updates))
                cur.executemany(update_query, statements)
                con.commit()
                statements = []

        if len(statements) >= 1:
            logger.info("geocoding with ban... %i of %i done", count, len(updates))
            cur.executemany(update_query, statements)
            con.commit()
        cur.close()
        con.close()

    @timeit
    def validate_coordinates(self):
        con, cur = import_util.create_cursor()
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
        cur.close()
        con.close()

    @timeit
    def run_geocoding_jobs(self, geocoding_jobs):
        adresses_not_geolocated[:] = []
        coordinates_updates[:] = []
        pool = Pool(processes=pool_size)
        for siret, full_address, initial_coordinates, city_code in geocoding_jobs:
            unit = GeocodeUnit(siret, full_address, coordinates_updates, initial_coordinates, city_code)
            pool.apply_async(unit.find_coordinates_for_address)
        pool.close()
        pool.join()
        logger.info("run geocoding jobs : collected {} coordinates on {} jobs, need to geocode {}".format(
            len(coordinates_updates),
            len(geocoding_jobs),
            len(adresses_not_geolocated)
        ))
        return adresses_not_geolocated

    @timeit
    def run_missing_geocoding_jobs(self,csv_max_rows=80000):
        # The CSV file to send to API must not be > 8mb (https://adresse.data.gouv.fr/api)
        # This line :"03880702000011,2 RUE DE LA TETE NOIRE 14700 FALAISE,14258"
        # was copied 100000 times in a file, and the size was 5.77 MB,
        # it seems ok to set it to ~80000 / 100000

        csv_path_prefix = '/tmp/csv_geocoding_'
        csv_files = []
        for start in range(0, len(adresses_not_geolocated), csv_max_rows):
            end = start + csv_max_rows
            csv_path = "{}-{}-{}.csv".format(csv_path_prefix, start, end)
            with open(csv_path, 'w') as resultFile:
                wr = csv.writer(resultFile, dialect='excel')
                wr.writerow(("siret", "full_address", "city_code"))
                wr.writerows(adresses_not_geolocated[start:end])
            csv_files.append(csv_path)
            logger.debug("wrote CSV file to %s", csv_path)

        pool = Pool(processes=pool_size)
        for csv_path in csv_files:
            pool.apply_async(self.get_geocode_from_api(csv_path))

        pool.close()
        pool.join()

        return coordinates_updates

    def get_geocode_from_api(self, csv_path):
        #curl -X POST -F data=@path/to/file.csv -F columns=voie columns=ville -F
        # citycode=ma_colonne_code_insee https://api-adresse.data.gouv.fr/search/csv/

        BASE = "http://api-adresse.data.gouv.fr/search/csv/"

        files = {'data': open(csv_path, 'rb')}
        values = {'columns':'full_address', 'city_code':'city_code'}

        response = session.post(BASE, files=files, data=values)
        response.close()

        if response.status_code == 200:
            try:
                decoded_content = response.content.decode('utf-8')
                df_geocodes = pd.read_csv(io.StringIO(decoded_content))

                for index, row in df_geocodes.iterrows():
                    if not numpy.isnan(row.latitude):
                        coordinates = [row.longitude, row.latitude]
                        geolocation = Geolocation(
                            full_address=row.full_address,
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
                        if coordinates:
                            GEOCODING_STATS['updatable_coordinates'] = GEOCODING_STATS.get('updatable_coordinates', 0) + 1
                            coordinates_updates.append([row.siret, coordinates])
                    else:
                        GEOCODING_STATS['coordinates_not_found'] = GEOCODING_STATS.get('coordinates_not_found', 0) + 1
            except ValueError:
                logger.warning('ValueError in json-ing features result %s', response.text)


    @timeit
    def run(self):
        logger.info("starting geocoding task...")
        geocoding_jobs = self.create_geocoding_jobs()
        logger.info("requesting BAN for all the adresses we need to geocode for...")
        self.run_geocoding_jobs(geocoding_jobs)
        self.run_missing_geocoding_jobs()
        logger.info("updating coordinates...")
        self.update_coordinates(coordinates_updates)
        logger.info("updated %i coordinates !", len(coordinates_updates))
        logger.info("GEOCODING_STATS = %s", GEOCODING_STATS)
        logger.info("validating coordinates...")
        self.validate_coordinates()
        logger.info("validated coordinates !")
        logger.info("completed geocoding task.")


class GeocodeUnit(object):

    def __init__(self, siret, address, updates, initial_coordinates, city_code):
        self.siret = siret
        self.full_address = address
        self.updates = updates
        self.initial_coordinates = initial_coordinates
        self.city_code = city_code

    def find_coordinates_for_address(self):
        """
        finding coordinates for an address based on the BAN (base d'adresses nationale),
        an online governmental service.
        """
        coordinates = None
        # FIXME refer to settings.API_ADRESS_BASE_URL and make sure we don't
        # make real requests in unit tests
        # Documentation API adresse data gouv : https://adresse.data.gouv.fr/api
        geolocation = Geolocation.get(self.full_address)
        if geolocation:
            # coordinates were already queried and cached before
            coordinates = [geolocation.x, geolocation.y]
            GEOCODING_STATS['cache_hits'] = GEOCODING_STATS.get('cache_hits', 0) + 1
        else:
            adresses_not_geolocated.append([self.siret, self.full_address, self.city_code])
            GEOCODING_STATS['cache_misses'] = GEOCODING_STATS.get('cache_misses', 0) + 1
        if coordinates:
            if coordinates == self.initial_coordinates:
                GEOCODING_STATS['unchanged_coordinates'] = GEOCODING_STATS.get('unchanged_coordinates', 0) + 1

def run_main():
    geocode_task = GeocodeJob()
    geocode_task.run()

if __name__ == "__main__":
    run_main()