import os
import gzip
import bz2
import re
import subprocess
from datetime import datetime
import logging
from functools import lru_cache
import traceback

import MySQLdb as mdb
from sqlalchemy import create_engine

from labonneboite.common import departements as dpt
from labonneboite.common.util import timeit
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.models.computing import ImportTask, HistoryImporterJobs, StatusJobExecution
from labonneboite.common.database import DATABASE
from labonneboite.common import encoding as encoding_util
from labonneboite.common.env import get_current_env, ENV_DEVELOPMENT
from labonneboite.common.database import db_session

logging.basicConfig(level=logging.INFO, format='%(message)s')

logger = logging.getLogger('main')

TRANCHE_AGE_SENIOR = "51-99"
TRANCHE_AGE_JUNIOR = "00-25"
TRANCHE_AGE_MIDDLE = "26-50"

OFFICE_FLAGS = ['flag_alternance', 'flag_junior', 'flag_senior', 'flag_handicap']


class InvalidRowException(Exception):
    pass

class InvalidSiretException(Exception):
    pass

class InvalidZipCodeException(Exception):
    pass


def create_cursor():
    con = mdb.connect(host=DATABASE['HOST'], port=DATABASE['PORT'],
                      user=DATABASE['USER'], passwd=DATABASE['PASSWORD'],
                      db=DATABASE['NAME'], use_unicode=True, charset="utf8")
    cur = con.cursor()
    return con, cur

def create_sqlalchemy_engine():
    user = DATABASE['USER']
    host = DATABASE['HOST']
    port = str(DATABASE['PORT'])
    db_name = DATABASE['NAME']
    db_password = DATABASE['PASSWORD']
    
    connexion_url = (f'mysql://{user}:{db_password}@{host}:{port}/{db_name}?charset=utf8mb4')

    #connexion_url = ('mysql://'+DATABASE['USER']+':%s@'+\
    #                DATABASE['HOST']+':'+str(DATABASE['PORT'])+\
    #                '/'+DATABASE['NAME']) % urllib.parse.quote_plus(DATABASE['PASSWORD'])

    engine = create_engine(connexion_url)

    return engine.connect()


def check_for_updates(input_folder):
    """
    do we have a new file we haven't processed yet in the input folder?
    """
    new_files = []
    for name in os.listdir(input_folder):
        full_name = os.path.join(input_folder, name)
        if not is_processed(full_name):
            new_files.append(full_name)
        else:
            logger.info("file %s was already processed and will thus be ignored", full_name)
    new_files.sort()
    return new_files


def get_backup_files_list(backup_folder, filename):
    start_of_file = f"{filename}_backup_"
    end_file = ".sql.gz"
    backup_files_list = []
    for file in os.listdir(backup_folder):
        if file.startswith(start_of_file) and file.endswith(end_file):
            backup_files_list.append(os.path.join(backup_folder,file))
    
    return backup_files_list

@timeit
def back_up(backup_folder, table, filename, timestamp, new_table_name=None):
    timestamp_filename = '%s_backup_%s.sql.gz' % (filename, timestamp)
    backup_filename = os.path.join(backup_folder, timestamp_filename)
    password_statement = "-p'%s'" % DATABASE['PASSWORD']
    logger.info("backing up table %s into %s", table, backup_filename)
    if new_table_name:
        table_new = new_table_name
    else:
        table_new = table

    # sed command from
    # https://stackoverflow.com/questions/8042723/mysqldump-can-you-change-the-name-of-the-table-youre-inserting-into
    # to rename table name on the fly,
    # useful in the case of deploy_data to allow zero downtime atomic table swap of table etablissements
    subprocess.check_call(
        """mysqldump -u %s %s --host %s --port %d %s %s | sed 's/`%s`/`%s`/g' | gzip > %s""" % (
            DATABASE['USER'],
            password_statement,
            DATABASE['HOST'],
            DATABASE['PORT'],
            DATABASE['NAME'],
            table,
            table,
            table_new,
            backup_filename),
        shell=True)

    logger.info("finished back up !")
    return backup_filename


def is_processed(filename):
    """
    an input file can be in different states,
    in order to track whether its contents were imported or not.
    This function lets us know whether contents were imported or not.
    """
    # To make run impact retour emploi project and importer project
    # There are 2 DPAE files
    #  lbb_xdpdpae_delta_201511102200.csv ==> Impact retour emploi
    #  lbb_xdpdpae_delta_201611102200.csv ==> Importer
    # When we are in local dev, we don't want the importer to use 
    #  lbb_xdpdpae_delta_201511102200.csv, so we will say that it's an alreay processed file
    if get_current_env() == ENV_DEVELOPMENT and filename == "lbb_xdpdpae_delta_201511102200.csv":
        return True

    import_tasks = ImportTask.query.filter(
        ImportTask.filename == os.path.basename(filename),
        ImportTask.state >= ImportTask.FILE_READ).all()
    return bool(import_tasks)


def check_runnable(filename, file_type):
    patterns = {
        'dpae': 'lbb_xdpdpae_delta_.*',
        'etablissements': 'lbb_etablissement_full_.*',
        'lba-app': '.*ExtractAPP.csv',
        'lba-pro': '.*ExtractPRO.csv'
    }
    base_name = os.path.basename(filename)
    return re.match(patterns[file_type], base_name) and not is_processed(base_name)


def detect_runnable_file(file_type, bulk=False):
    logger.info("detect runnable file for file type: %s", file_type)
    filenames = []
    for filename in check_for_updates(importer_settings.INPUT_SOURCE_FOLDER):
        logger.info("inspecting file %s", filename)
        if check_runnable(filename, file_type):
            if not bulk:
                logger.info("will run this file : %s", filename)
                return filename
            else:
                filenames.append(filename)
    if filenames:
        logger.info("will run this file : %s", filenames)
        return filenames
    else:
        logger.info("no runnable file found!")
        return None


@timeit
def reduce_scores_into_table(
        description,
        departements,
        target_table,
        select_fields,
    ):
    """
    Analog to a Map/Reduce operation.
    We have "etablissements" in MySQL tables for each departement.
    This step combines all etablissements into a single MySQL table, ready to be exported.

    WARNING : this drops the original target_table and repopulates it from scratch

    FIXME parallelize and optimize performance
    """
    logger.info("reducing scores %s ...", description)
    errors = successes = 0

    # empty existing table before filling it again
    run_sql_script("delete from %s" % target_table)

    for departement in departements:
        departement_table = "etablissements_%s" % departement
        query = """insert into %s select %s from %s""" % (
            target_table, select_fields, departement_table)
        try:
            run_sql_script(query)  # FIXME
            successes += 1
        except mdb.ProgrammingError:
            logger.error("an error happened while reducing departement=%s description=%s using query [%s]",
                departement, description, query)
            errors += 1
    if errors > importer_settings.MAXIMUM_COMPUTE_SCORE_JOB_FAILURES:
        msg = "too many job failures: %s (max %s) vs %s successes" % (errors,
            importer_settings.MAXIMUM_COMPUTE_SCORE_JOB_FAILURES, successes)
        raise Exception(msg)
    logger.info("score reduction %s finished, all data available in table %s",
                description, target_table)


def get_shared_select_fields():
    return (
        """siret, raisonsociale, enseigne, codenaf,
        trancheeffectif, numerorue, libellerue, codepostal,
        tel, email, website, """
        + "0, 0, 0, 0, " # stand for flag_alternance, flag_junior, flag_senior, flag_handicap
        + "0, " # stands for has_multi_geolocation
        + "codecommune, "
        + "0, 0, " # stands for coordinates_x, coordinates_y
        + "departement, score"
        )

def get_select_fields_for_main_db():
    """
    These fields should exactly match (and in the same order)
    the fields in "DESC etablissements_exportable;" (using MySQL CLI)
    """
    return (
        get_shared_select_fields()
        + ', ""'  # stands for email_alternance
        + ', score_alternance'
        + ', "", "", "", ""'  # stand for social_network, phone_alternance, website_alternance, contact_mode
        + ', flag_poe_afpr, flag_pmsmp'
    )


def get_select_fields_for_backoffice():
    """
    These fields should exactly match (and in the same order)
    the fields in "DESC etablissements_backoffice;" (using MySQL CLI)
    """
    fields = get_shared_select_fields()
    fields += ", effectif, score_regr"
    for i in range(7, 0, -1):  # [7, 6, 5, 4, 3, 2, 1]
        fields += ", `dpae-period-%s`" % i
    fields += ", score_alternance"
    for i in range(7, 0, -1):  # [7, 6, 5, 4, 3, 2, 1]
        fields += ", `alt-period-%s`" % i
    fields += ', flag_poe_afpr, flag_pmsmp'
    return fields


@timeit
def reduce_scores_for_main_db(departements):
    reduce_scores_into_table(
        description="[main_db]",
        departements=departements,
        target_table=importer_settings.SCORE_REDUCING_TARGET_TABLE,
        select_fields=get_select_fields_for_main_db(),
    )


@timeit
def reduce_scores_for_backoffice(departements):
    reduce_scores_into_table(
        description="[backoffice]",
        departements=departements,
        target_table=importer_settings.BACKOFFICE_ETABLISSEMENT_TABLE,
        select_fields=get_select_fields_for_backoffice(),
    )


@timeit
def clean_temporary_tables():
    logger.info("clean all departement database tables...")
    departements = dpt.DEPARTEMENTS
    for departement in departements:
        departement_table = "etablissements_%s" % departement
        drop_table_query = "drop table if exists %s" % departement_table
        run_sql_script(drop_table_query)


def get_fields_from_csv_line(line, delimiter='|'):
    # get rid of invisible space characters (\xc2) if present
    line = line.strip().replace('\xc2', '')
    fields = [encoding_util.sanitize_string(f) for f in line.split(delimiter)]

    # The CSV files which are now extracted can contain either '' OR 'NULL' when there are null values.
    # We need to replace 'NULL' values with an empty string
    fields = ['' if field=='NULL' else field for field in fields]

    return fields

def parse_alternance_line(line):
    fields = get_fields_from_csv_line(line, delimiter=';')
    required_fields = 4
    if len(fields) != required_fields:  # an assert statement here does not work from nosetests
        msg = f"found {len(fields)} fields instead of {required_fields} in line: {line}"
        logger.error(msg)
        raise InvalidRowException(msg)

    siret = fields[0]
    if len(siret) != 14:
        #Problem in data sent : the siret must be parsed to int somewhere in the process, and the first possible 3 '0' are skipped...
        if len(siret) <= 13 and len(siret) >= 11:
            zero_missing = 14 - len(siret)
            siret = (zero_missing * '0' ) + siret
        else:
            raise InvalidSiretException(f"The siret {siret} is not valid")

    hiring_date_raw = fields[1]
    hiring_date = datetime.strptime(hiring_date_raw, "%d/%m/%Y")

    zip_code = fields[3]
    departement = get_departement_from_zipcode(zip_code)

    return siret, hiring_date, departement

def parse_dpae_line(line):
    fields = get_fields_from_csv_line(line)
    required_fields = 27
    if len(fields) != required_fields:  # an assert statement here does not work from nosetests
        msg = ("found %s fields instead of %s in line: %s" % (
            len(fields), required_fields, line
        ))
        logger.error(msg)
        raise InvalidRowException(msg)

    siret = fields[0]


    hiring_date_raw = fields[7]
    try:
        hiring_date = datetime.strptime(hiring_date_raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        hiring_date = datetime.strptime(hiring_date_raw, "%Y-%m-%d %H:%M:%S.0")

    try:
        zipcode = int(fields[3])
    except ValueError:
        zipcode = None

    departement = get_departement_from_zipcode(zipcode)

    try:
        contract_type = int(fields[8])
    except ValueError:
        contract_type = None

    try:
        contract_duration = int(fields[20])
    except ValueError:
        contract_duration = None

    iiann = fields[21]

    def remove_exotic_characters(text):
        return ''.join(i for i in text if ord(i) < 128)

    choices = {
        "- de 26 ans": TRANCHE_AGE_JUNIOR,
        "de 26 ans ? 50 ans": TRANCHE_AGE_MIDDLE,
        "+ de 50 ans": TRANCHE_AGE_SENIOR
    }

    handicap_label = fields[22]

    try:
        tranche_age = choices[remove_exotic_characters(fields[23])]
    except KeyError:
        raise ValueError("unknown tranche_age %s" % fields[23])

    try:
        duree_pec = int(fields[24])
    except ValueError:
        duree_pec = None

    return (siret, hiring_date, zipcode, contract_type, departement,
        contract_duration, iiann, tranche_age, handicap_label, duree_pec)


def get_file_extension(filename):
    _, file_extension = os.path.splitext(filename)
    return file_extension


def get_open_file(filename):
    file_extension = get_file_extension(filename)
    if file_extension == ".gz":
        open_file = gzip.open
    elif file_extension == ".bz2":
        open_file = bz2.BZ2File
    elif file_extension == ".csv":
        open_file = open
    else:
        raise "unknown file extension"
    return open_file


def get_reader(filename):
    open_file = get_open_file(filename)
    return open_file(filename, "rb")


@lru_cache(maxsize=128*1024)
def get_departement_from_zipcode(zipcode):
    zipcode = str(zipcode).strip()

    if len(zipcode) == 1:
        departement = "0%s" % zipcode[0]
    elif len(zipcode) == 2:
        departement = zipcode
    elif len(zipcode) == 4:
        departement = "0%s" % zipcode[0]
    elif len(zipcode) == 5:
        departement = zipcode[:2]
    else:
        departement = None

    if departement in ["2A", "2B"]:  # special case of Corsica
        departement = "20"
    return departement


def run_sql_script(sql_script):
    con, cur = create_cursor()

    for query in sql_script.split(';'):
        query = query.strip()
        if len(query) >= 1:
            cur.execute(query)
            con.commit()
    cur.close()
    con.close()

IMPORTER_JOBS_ORDER = [
    'check_etablissements',
    'extract_etablissements',
    'check_dpae',
    'extract_dpae',
    'compute_scores',
    'validate_scores',
    'geocode',
    'populate_flags'
]

def get_previous_job_info(job_name):
    index = IMPORTER_JOBS_ORDER.index(job_name)
    previous_job_name = None
    previous_job_done = False
    if index == 0: # First job, there is no job to start previously
        previous_job_done = True
    else:
        previous_job_name = IMPORTER_JOBS_ORDER[index-1]
        previous_job_done = HistoryImporterJobs.is_job_done(job=previous_job_name)

    return {"name": previous_job_name, "is_completed": previous_job_done}

def history_importer_job_decorator(script_name):
    def decorator(function_to_execute):
        def fonction_with_history():
            # Get the job_name argument and remove the .py extension in the job name
            job = script_name.split('.')
            if job[1] == 'py':
                job_name = job[0]
            else:
                raise BadDecoratorUse

            # Check that the previous job is done to start this one
            # If the previous job is not done, it will raise an exception
            info_previous_job = get_previous_job_info(job_name)
            if info_previous_job['is_completed'] is False:
                print(f"The previous job '{info_previous_job['name']}' is not done ")
                raise PreviousJobNotDone
            else:
                print(f"The previous job '{info_previous_job['name']}' is done. We can run this one ! ")

            #Save in database the start of this job
            start_date = datetime.now()
            history = HistoryImporterJobs(
                start_date = start_date,
                end_date = None,
                job_name = job_name,
                status = StatusJobExecution['start'],
                exception = None,
                trace_log = None
            )
            db_session.add(history)
            db_session.commit()

            #If the job is done, we save it with done status
            try:
                result = function_to_execute()
                history.end_date = datetime.now()
                history.status = StatusJobExecution['done']
                db_session.commit()
            #Else if an error occured, we raise the exception, and save it in the DB with a failed status
            except Exception as e:
                history.end_date = datetime.now()
                history.exception = type(e).__name__
                history.trace_log = traceback.format_exc()
                history.status = StatusJobExecution['error']
                db_session.commit()
                raise

            return result
        return fonction_with_history
    return decorator

class BadDecoratorUse(Exception):
    print("this decorator is used for importer jobs")
    pass

class PreviousJobNotDone(Exception):
    pass