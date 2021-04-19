"""
Etablissements are imported for Pole Emploi databases without geo coordinates.

This module assists in finding and assigning geo coordinates to etablissements.

Documentation about the open data API we use here:
https://adresse.data.gouv.fr/api
https://adresse.data.gouv.fr/faq
"""
from multiprocessing import Manager, Pool
import io
import os
import csv
import time
import requests
from sqlalchemy.exc import IntegrityError
import pandas as pd
import numpy

from labonneboite.common.database import db_session
from labonneboite.common.load_data import load_city_codes
from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.importer.util import history_importer_job_decorator
from labonneboite.common.util import timeit
from labonneboite.importer.models.computing import Geolocation
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger

DEBUG_MODE = False

pool_size = 8
connection_limit = pool_size
adapter = requests.adapters.HTTPAdapter(pool_connections=connection_limit,
                                        pool_maxsize=connection_limit,
                                        max_retries=4)
session = requests.session()
session.mount('http://', adapter)
jobs = []

CITY_NAMES = load_city_codes()

# Shared variables between processes for multithreading
manager = Manager()

# list to store the geolocations not saved in cache
adresses_not_geolocated = manager.list()

# list to store the coordinates to update
coordinates_updates = manager.list()

# dict which will store stats about the current geocoding
GEOCODING_STATS = manager.dict()

# list which will store names of CSV returned by API and stored
csv_api_back = manager.list()


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

        full_address = "%s %s %s %s" % (
            street_number, street_name, zipcode, city)
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
        if DEBUG_MODE:
            #query += "WHERE coordinates_x = 0 and coordinates_y = 0"
            query += "ORDER BY RAND() LIMIT 100000"
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
                full_address = self.get_full_adress(
                    street_number, street_name, zipcode, city)
                initial_coordinates = [coordinates_x, coordinates_y]
                geocoding_jobs.append(
                    [siret, full_address, initial_coordinates, codecommune])
            except IncorrectAdressDataException:
                logger.warning("incorrect address for %s %s %s %s",
                               street_number, street_name, zipcode, city)
            count += 1
            GEOCODING_STATS['jobs'] = GEOCODING_STATS.get('jobs', 0) + 1
            if not count % 10000:
                logger.info(
                    "loading geocoding jobs from db... loaded %s rows", count)
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

        logger.info("Nb of offices to update : {}".format(len(updates)))

        for siret, coordinates in updates:
            count += 1
            statements.append([coordinates[0], coordinates[1], siret])
            if len(statements) == 1000:
                logger.info("geocoding with ban... %i of %i done",
                            count, len(updates))
                cur.executemany(update_query, statements)
                con.commit()
                statements = []

        if len(statements) >= 1:
            logger.info("geocoding with ban... %i of %i done",
                        count, len(updates))
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
    def run_geocoding_jobs(self, geocoding_jobs, disable_multithreading=True):
        adresses_not_geolocated[:] = []
        coordinates_updates[:] = []

        logger.info("Nombre de geocoding jobs : {}".format(
            len(geocoding_jobs)))

        if disable_multithreading:
            for siret, full_address, initial_coordinates, city_code in geocoding_jobs:
                self.find_coordinates_for_address(
                    siret, full_address, initial_coordinates, city_code)
        else:
            pool = Pool(processes=pool_size)
            for siret, full_address, initial_coordinates, city_code in geocoding_jobs:
                pool.apply_async(self.find_coordinates_for_address,
                                 (siret, full_address, initial_coordinates, city_code,))
            pool.close()
            pool.join()

        logger.info("run geocoding jobs : collected {} coordinates on {} jobs, need to geocode {}".format(
            GEOCODING_STATS.get('cache_hits', 0),
            len(geocoding_jobs),
            len(adresses_not_geolocated)
        ))
        return adresses_not_geolocated

    def find_coordinates_for_address(self, siret, full_address, initial_coordinates, city_code):
        coordinates = None
        geolocation = Geolocation.get(full_address)
        if geolocation:
            # coordinates were already queried and cached before
            coordinates = [geolocation.x, geolocation.y]
            GEOCODING_STATS['cache_hits'] = GEOCODING_STATS.get(
                'cache_hits', 0) + 1
            if coordinates == initial_coordinates:
                GEOCODING_STATS['unchanged_coordinates'] = GEOCODING_STATS.get(
                    'unchanged_coordinates', 0) + 1
            else:
                GEOCODING_STATS['existing_coordinates_to_update'] = GEOCODING_STATS.get(
                    'existing_coordinates_to_update', 0) + 1
                coordinates_updates.append(
                    [siret, coordinates])
        else:
            adresses_not_geolocated.append(
                [siret, full_address, city_code])
            GEOCODING_STATS['cache_misses'] = GEOCODING_STATS.get(
                'cache_misses', 0) + 1

    @timeit
    def run_missing_geocoding_jobs(self, csv_max_rows=5000, disable_multithreading=False):
        # The CSV file to send to API must not be > 8mb (https://adresse.data.gouv.fr/api)
        # This line :"03880702000011,2 RUE DE LA TETE NOIRE 14700 FALAISE,14258"
        # was copied 100000 times in a file, and the size was 5.77 MB,
        # it seems ok to set it to ~80000 / 100000
        # --> After multiple tests, if we want to multithread this, we need to set it to 5000, not more

        csv_path_prefix = '/tmp/csv_geocoding'
        csv_files = []
        csv_api_back[:] = []
        for start in range(0, len(adresses_not_geolocated), csv_max_rows):
            end = start + csv_max_rows
            csv_path = "{}-{}-{}.csv".format(csv_path_prefix, start, end)
            with open(csv_path, 'w') as resultFile:
                wr = csv.writer(resultFile, dialect='excel')
                wr.writerow(("siret", "full_address", "city_code"))
                wr.writerows(adresses_not_geolocated[start:end])
            csv_files.append(csv_path)
            GEOCODING_STATS['number created CSV'] = GEOCODING_STATS.get(
                'number created CSV', 0) + 1
            logger.debug("wrote CSV file to %s", csv_path)

        logger.info("GEOCODING_STATS = %s", GEOCODING_STATS)

        for csv_path in csv_files:
            self.get_csv_from_api(csv_path)

        logger.info("GEOCODING_STATS = %s", GEOCODING_STATS)

        if disable_multithreading:
            for csv_path in csv_api_back:
                self.get_geocode_from_csv(csv_path)
        else:
            pool = Pool(processes=pool_size)
            for csv_path in csv_api_back:
                pool.apply_async(self.get_geocode_from_csv, (csv_path,))
            pool.close()
            pool.join()

        logger.info("GEOCODING_STATS = %s", GEOCODING_STATS)

        return coordinates_updates

    # Send one CSV to the API, and save the CSV which is sent back with the coordinates
    def get_csv_from_api(self, csv_path):
        # curl -X POST -F data=@path/to/file.csv -F columns=voie columns=ville -F
        # citycode=ma_colonne_code_insee https://api-adresse.data.gouv.fr/search/csv/

        logger.info("find coordinates on CSV {}".format(csv_path))

        BASE = "http://api-adresse.data.gouv.fr/search/csv/"

        files = {'data': open(csv_path, 'rb')}
        values = {'columns': 'full_address', 'city_code': 'city_code'}

        # FIXME : Ugly way to wait for the API to be OK with our requests
        retry_counter = 5
        job_done = False

        while not job_done and retry_counter > 0:
            response = session.post(BASE, files=files, data=values)
            response.close()
            logger.info('STATUS RESPONSE : {} pour le csv {}'.format(
                response.status_code, csv_path))
            if response.status_code == 200:
                job_done = True
            else:
                retry_counter -= 1
                time.sleep(5)

        if job_done:
            GEOCODING_STATS['API status 200 for CSV'] = GEOCODING_STATS.get(
                'API status 200 for CSV', 0) + 1
            try:
                logger.info(
                    "API addr gouv response on CSV {} OK".format(csv_path))
                decoded_content = response.text
                df_geocodes = pd.read_csv(io.StringIO(
                    decoded_content), dtype={'siret': str})
                csv_api_back_path = csv_path + '-api'
                df_geocodes.to_csv(csv_api_back_path, index=False)
                csv_api_back.append(csv_api_back_path)
                logger.info(
                    "Wrote CSV sent back by API : {}".format(csv_api_back_path))
            except ValueError:
                logger.warning(
                    'ValueError in json-ing features result %s', response.text)
        else:
            logger.info("The csv {} was not saved correctly".format(csv_path))
        logger.info("GEOCODING_STATS = {} for CSV {}".format(
            GEOCODING_STATS, csv_path))

    # Takes the CSV which has been sent by the API with coordinates, and will parse the CSV
    def get_geocode_from_csv(self, csv_api_path):
        logger.info("Parsing CSV sent back by API : {}".format(csv_api_path))
        df_geocodes = pd.read_csv(csv_api_path, dtype={'siret': str})
        for index, row in df_geocodes.iterrows():
            if not numpy.isnan(row.latitude):
                coordinates = [row.longitude, row.latitude]
                geolocation = Geolocation.get(row.full_address)
                # There should not be an already existing geolocation
                # but working on this job, makes you know that sometimes,
                # the coordinates related to a siret do not update, but the geolocation is still added
                # in the database
                if geolocation:
                    logger.info("Geolocation already found")
                    GEOCODING_STATS['updatable_coordinates'] = GEOCODING_STATS.get(
                        'updatable_coordinates', 0) + 1
                    coordinates_updates.append(
                        [row.siret, coordinates])
                else:
                    logger.info("Geolocation not found")
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
                        GEOCODING_STATS['flushes'] = GEOCODING_STATS.get(
                            'flushes', 0) + 1
                    except IntegrityError:
                        # happens when a job tries to insert an already existing full_address
                        # rollback needed otherwise db_session is left
                        # in a state unusable by the other parallel jobs
                        db_session.rollback()
                        GEOCODING_STATS['rollbacks'] = GEOCODING_STATS.get(
                            'rollbacks', 0) + 1
                    if coordinates:
                        GEOCODING_STATS['updatable_coordinates'] = GEOCODING_STATS.get(
                            'updatable_coordinates', 0) + 1
                        coordinates_updates.append(
                            [row.siret, coordinates])
            else:
                GEOCODING_STATS['coordinates_not_found'] = GEOCODING_STATS.get(
                    'coordinates_not_found', 0) + 1

    @timeit
    def run(self):
        logger.info("starting geocoding task...")
        geocoding_jobs = self.create_geocoding_jobs()
        logger.info(
            "requesting BAN for all the adresses we need to geocode for...")
        self.run_geocoding_jobs(geocoding_jobs)
        if DEBUG_MODE:
            self.run_missing_geocoding_jobs(csv_max_rows=500)
        else:
            self.run_missing_geocoding_jobs()
        logger.info("updating coordinates...")
        self.update_coordinates(coordinates_updates)
        logger.info("updated %i coordinates !", len(coordinates_updates))
        logger.info("validating coordinates...")
        self.validate_coordinates()
        logger.info("validated coordinates !")
        logger.info("completed geocoding task.")

@history_importer_job_decorator(os.path.basename(__file__))
def run_main():
    geocode_task = GeocodeJob()
    geocode_task.run()


if __name__ == "__main__":
    run_main()
