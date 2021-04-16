"""
Extracts data from CSV file into a MySQL table.

It is assumed the extract function will not be called twice for the same file
(otherwise duplicate records will be created). This should be taken care of by the caller.

For each extraction, we record its extraction datetime and its most recent dpae date.
"""
import re
import time
from datetime import datetime
import sys
from sqlalchemy.exc import OperationalError
import os
from sqlalchemy import func
import pandas
import traceback

from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.common.util import timeit
from labonneboite.importer.util import parse_alternance_line, InvalidRowException, InvalidSiretException, InvalidZipCodeException, history_importer_job_decorator
from labonneboite.importer.models.computing import DpaeStatistics, ImportTask, Hiring
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger
from labonneboite.common.database import db_session


class ApprentissageExtractJob(Job):
    import_type = ImportTask.APPRENTISSAGE
    table_name = settings.HIRING_TABLE

    def __init__(self, filename, contract_type = "APPRENTISSAGE"):
        self.input_filename = filename
        self.contract_name = contract_type
        if contract_type == 'APPRENTISSAGE':
            self.file_type = DpaeStatistics.APR
            self.contract_type = Hiring.CONTRACT_TYPE_APR
        elif contract_type == 'CONTRAT_PRO':
            self.file_type = DpaeStatistics.PRO 
            self.contract_type = Hiring.CONTRACT_TYPE_CP
        self.last_historical_data_date_in_file = None
        self.invalid_row_errors = 0
        self.invalid_siret_errors = 0
        self.invalid_zipcode_errors = 0

    @timeit
    def run_task(self):
        date_insertion = datetime.now()
        logger.info("extracting %s ", self.input_filename)
        # this pattern matches the first date
        # e.g. '20200803ExtractApp'
        # will match 20200803
        date_string = self.input_filename.split('/')[-1][0:8] 
        try:
            self.last_historical_data_date_in_file = datetime.strptime(date_string, "%Y%m%d")
        except ValueError:
            raise Exception("couldn't find a date pattern in filename. filename should be \
                like 20200803ExtractApp.csv")

        count = 0
        statements = []
        something_new = False
        query = """
            INSERT into %s(
                siret,
                hiring_date,
                contract_type,
                departement,
                contract_duration,
                iiann,
                tranche_age,
                handicap_label,
                duree_pec
                )
            values(%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)
        """ % settings.HIRING_TABLE
        imported_alternance_contracts = 0
        imported_alternance_contracts_distribution = {}
        not_imported_alternance_contracts = 0

        last_historical_data_date_in_db = db_session.query(func.max(Hiring.hiring_date))\
                                                            .filter(Hiring.contract_type == self.contract_type).first()[0]

        logger.info("will now extract all alternance contracts with hiring_date between %s and %s",
                    last_historical_data_date_in_db, self.last_historical_data_date_in_file)

        with import_util.get_reader(self.input_filename) as myfile:
            con, cur = import_util.create_cursor()
            header_line = myfile.readline().strip()   # FIXME detect column positions from header
            
            if b"SIRET" not in header_line:
                logger.debug(header_line)
                raise Exception("wrong header line")

            for line in myfile:
                line = line.decode()
                count += 1
                if not count % 10000:
                    logger.debug("reading line %i", count)
                    try:
                        try:
                            cur.executemany(query, statements)
                        except OperationalError:  # retry once in case of deadlock error
                            time.sleep(10)
                            cur.executemany(query, statements)
                        statements = []
                        con.commit()
                        something_new = True
                    except:
                        logger.error("error in executing statement into hirings table: %s", sys.exc_info()[1])
                        statements = []
                        raise
                try:
                    siret, hiring_date, departement = parse_alternance_line(line)
                except InvalidRowException:
                    logger.info("invalid_row met at row: %i", count)
                    self.invalid_row_errors += 1
                    continue
                except InvalidSiretException:
                    error_message = traceback.format_exc()
                    logger.info("invalid siret met at row: %i", count)
                    logger.info(error_message)
                    self.invalid_siret_errors += 1
                    continue
                except InvalidZipCodeException:
                    logger.info("invalid zip code met at row: %i", count)
                    self.invalid_zipcode_errors += 1
                    continue
                
                # This part of code is useless : 
                #   The data used has a lot of late contracts inputs
                #   So we have to insert ALL the contracts from different dates

                #  alternance_contract_should_be_imported = (
                #      hiring_date > last_historical_data_date_in_db 
                #      and hiring_date <= self.last_historical_data_date_in_file
                #)

                if hiring_date <= self.last_historical_data_date_in_file:
                    statement = (
                        siret,
                        hiring_date,
                        self.contract_type,
                        departement,
                        None, #contract_duration
                        None, #iiann
                        None, #tranche_age
                        None, #handicap_label
                        None,  #duree_pec
                        date_insertion

                    )
                    statements.append(statement)
                    imported_alternance_contracts += 1

                    if hiring_date.year not in imported_alternance_contracts_distribution:
                        imported_alternance_contracts_distribution[hiring_date.year] = {}
                    if hiring_date.month not in imported_alternance_contracts_distribution[hiring_date.year]:
                        imported_alternance_contracts_distribution[hiring_date.year][hiring_date.month] = {}
                    if hiring_date.day not in imported_alternance_contracts_distribution[hiring_date.year][hiring_date.month]:
                        imported_alternance_contracts_distribution[hiring_date.year][hiring_date.month][hiring_date.day] = 0
                    imported_alternance_contracts_distribution[hiring_date.year][hiring_date.month][hiring_date.day] += 1

        # run remaining statements
        try:
            cur.executemany(query, statements)
            something_new = True
        except:
            logger.error("error in executing statement into hirings table: %s", sys.exc_info()[1])
            raise

        logger.info(f"Types de contrats à importer : {self.contract_name}")
        logger.info(f"processed {count} lba_contracts...")
        logger.info(f"imported lba_contracts: {imported_alternance_contracts}")
        logger.info(f"not imported lba_contracts: {not_imported_alternance_contracts}")
        logger.info(f"zipcode errors: {self.invalid_zipcode_errors}")
        logger.info(f"invalid_row errors: {self.invalid_row_errors}")
        logger.info(f"invalid siret errors: {self.invalid_siret_errors}")
#        if self.zipcode_errors > settings.MAXIMUM_ZIPCODE_ERRORS:
#            raise IOError('too many zipcode errors')
#        if self.invalid_row_errors > settings.MAXIMUM_INVALID_ROWS:
#            raise IOError('too many invalid_row errors')

        con.commit()
        cur.close()
        con.close()

        try:
            statistics = DpaeStatistics(
                last_import=datetime.now(),
                most_recent_data_date=self.last_historical_data_date_in_file,
                file_type=self.file_type
            )
            db_session.add(statistics)
            db_session.commit()
            logger.info("First way to insert DPAE statistics in DB : OK")
        except OperationalError:
            # For an obscure reason, the DpaeStatistics way to insert does not work on the bonaparte server
            # So we insert it directly via an SQL query
            # This job has been broken for more than a year, only way to fix it : 
            db_session.rollback()
            last_import_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            most_recent_date = self.last_historical_data_date_in_file.strftime('%Y-%m-%d %H:%M:%S')
            query = f"insert into dpae_statistics (last_import, most_recent_data_date, file_type) values ('{last_import_date}','{most_recent_date}','{self.file_type}')"
            con, cur = import_util.create_cursor()
            cur.execute(query)
            con.commit()
            cur.close()
            con.close()
            logger.info("Second way to insert DPAE statistics in DB : OK")


        logger.info("finished importing dpae...")
        return something_new


@history_importer_job_decorator(os.path.basename(__file__))
def run_main():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    lba_app_filenames = import_util.detect_runnable_file("lba-app", bulk=True)
    for filename in lba_app_filenames:
        logger.info("PROCESSING %s" % filename)
        task_app = ApprentissageExtractJob(filename, contract_type = 'APPRENTISSAGE')
        task_app.run()

    lba_pro_filenames = import_util.detect_runnable_file("lba-pro", bulk=True)
    for filename in lba_pro_filenames:
        logger.info("PROCESSING %s" % filename)
        task_pro = ApprentissageExtractJob(filename, contract_type = 'CONTRAT_PRO')
        task_pro.run()

if __name__ == '__main__':
    run_main()
