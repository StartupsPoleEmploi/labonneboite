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
from sqlalchemy import func
import os

from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.common.util import timeit
from labonneboite.importer.util import parse_dpae_line, InvalidRowException, history_importer_job_decorator
from labonneboite.importer.models.computing import DpaeStatistics, ImportTask, Hiring
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger
from labonneboite.common.database import db_session
from labonneboite.importer.models.errors import DoublonException

class DpaeExtractJob(Job):
    file_type = DpaeStatistics.DPAE
    import_type = ImportTask.DPAE
    table_name = settings.HIRING_TABLE

    def __init__(self, filename):
        self.input_filename = filename
        self.last_historical_data_date_in_file = None
        self.zipcode_errors = 0
        self.invalid_row_errors = 0

    @timeit
    def run_task(self):
        date_insertion = datetime.now()
        logger.info("extracting %s ", self.input_filename)
        # this pattern matches the first date
        # e.g. 'lbb_xdpdpae_delta_201611102200.bz2'
        # will match 2018-09-12
        date_pattern = r'.*_(\d\d\d\d\d\d\d\d)\d\d\d\d' #We keep only the date in the file name, ex: 20190910 = 10th september 2019
        date_match = re.match(date_pattern, self.input_filename)
        if date_match:
            date_part = date_match.groups()[0]
            self.last_historical_data_date_in_file = datetime.strptime(date_part, "%Y%m%d")
            logger.debug("identified last_historical_data_date_in_file=%s", self.last_historical_data_date_in_file)
        else:
            raise Exception("couldn't find a date pattern in filename. filename should be \
                like lbb_xdpdpae_delta_YYYYMMDDHHMM.csv")

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
                duree_pec,
                date_insertion
                )
            values(%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)
        """ % settings.HIRING_TABLE
        imported_dpae = 0
        imported_dpae_distribution = {}
        not_imported_dpae = 0
        last_historical_data_date_in_db = db_session.query(func.max(Hiring.hiring_date)) \
                                        .filter(Hiring.contract_type.in_((Hiring.CONTRACT_TYPE_CDI,
                                                                          Hiring.CONTRACT_TYPE_CDD,
                                                                          Hiring.CONTRACT_TYPE_CTT))).first()[0]
        logger.info("will now extract all dpae with hiring_date between %s and %s",
                    last_historical_data_date_in_db, self.last_historical_data_date_in_file)

        with import_util.get_reader(self.input_filename) as myfile:
            con, cur = import_util.create_cursor()
            header_line = myfile.readline().strip()   # FIXME detect column positions from header
            if b"siret" not in header_line:
                logger.debug(header_line)
                raise Exception("wrong header line")
            for line in myfile:
                line = line.decode()
                count += 1
                if not count % 100000:
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
                        logger.error("error in executing statement into dpae table: %s", sys.exc_info()[1])
                        statements = []
                        raise
                try:
                    siret, hiring_date, _, contract_type, departement, contract_duration, \
                    iiann, tranche_age, handicap_label, duree_pec = parse_dpae_line(line)
                except ValueError:
                    self.zipcode_errors += 1
                    continue
                except InvalidRowException:
                    logger.info("invalid_row met at row: %i", count)
                    self.invalid_row_errors += 1
                    continue

                dpae_should_be_imported = (
                    hiring_date > last_historical_data_date_in_db 
                    and hiring_date <= self.last_historical_data_date_in_file
                    # For DPAE contracts we only keep all CDI, only long enough CDD (at least 31 days)
                    # and we ignore CTT.
                    and (
                        contract_type == Hiring.CONTRACT_TYPE_CDI
                        or (
                            contract_type == Hiring.CONTRACT_TYPE_CDD
                            and contract_duration is not None
                            and contract_duration > 31
                        )
                    )
                )

                if dpae_should_be_imported:
                    statement = (
                        siret,
                        hiring_date,
                        contract_type,
                        departement,
                        contract_duration,
                        iiann,
                        tranche_age,
                        handicap_label,
                        duree_pec,
                        date_insertion
                    )
                    statements.append(statement)
                    imported_dpae += 1

                    if hiring_date.year not in imported_dpae_distribution:
                        imported_dpae_distribution[hiring_date.year] = {}
                    if hiring_date.month not in imported_dpae_distribution[hiring_date.year]:
                        imported_dpae_distribution[hiring_date.year][hiring_date.month] = {}
                    if hiring_date.day not in imported_dpae_distribution[hiring_date.year][hiring_date.month]:
                        imported_dpae_distribution[hiring_date.year][hiring_date.month][hiring_date.day] = 0
                    imported_dpae_distribution[hiring_date.year][hiring_date.month][hiring_date.day] += 1
                else:
                    not_imported_dpae += 1

        # run remaining statements
        try:
            cur.executemany(query, statements)
            something_new = True
        except:
            logger.error("error in executing statement into dpae table: %s", sys.exc_info()[1])
            raise

        logger.info("processed %i dpae...", count)
        logger.info("imported dpae: %i", imported_dpae)
        logger.info("not imported dpae: %i", not_imported_dpae)
        logger.info("zipcode errors: %i", self.zipcode_errors)
        logger.info("invalid_row errors: %i", self.invalid_row_errors)
        if self.zipcode_errors > settings.MAXIMUM_ZIPCODE_ERRORS:
            raise IOError('too many zipcode errors')
        if self.invalid_row_errors > settings.MAXIMUM_INVALID_ROWS:
            raise IOError('too many invalid_row errors')
        logger.info("verifying good number of dpae imported.")
        query = "select count(*) from hirings h where hiring_date > %s and hiring_date <= %s and h.contract_type in (1,2,3)"
        cur.execute(query, [last_historical_data_date_in_db, self.last_historical_data_date_in_file])
        res = cur.fetchone()
        if res[0] != imported_dpae:
            raise DoublonException(f"Too many DPAE ({res[0]}) in DB compared to DPAE file ({imported_dpae}).")
        logger.info("verifying number of DPAE: OK.")
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
    dpae_filenames = import_util.detect_runnable_file("dpae", bulk=True)
    for filename in dpae_filenames:
        logger.info("PROCESSING %s" % filename)
        task = DpaeExtractJob(filename)
        task.run()


if __name__ == '__main__':
    run_main()
