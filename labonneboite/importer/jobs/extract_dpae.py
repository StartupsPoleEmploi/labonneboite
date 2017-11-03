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

from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.importer.util import timeit
from labonneboite.importer.util import parse_dpae_line, DepartementException, InvalidRowException
from labonneboite.importer.models.computing import DpaeStatistics, ImportTask
from labonneboite.conf import get_current_env, ENV_LBBDEV
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger


class DpaeExtractJob(Job):
    file_type = "dpae"
    import_type = ImportTask.DPAE
    table_name = settings.DPAE_TABLE

    def __init__(self, filename):
        self.input_filename = filename
        self.most_recent_data_date = None
        self.zipcode_errors = 0
        self.invalid_row_errors = 0

    # actually never used FIXME
    def print_dpae_distribution(self, imported_dpae_distribution):
        for year, _ in sorted(imported_dpae_distribution.items()):
            for month, _ in sorted(imported_dpae_distribution[year].items()):
                for day, count in sorted(imported_dpae_distribution[year][month].items()):
                    logger.info("year: %s, month: %s, day: %s, dpae count %s", year, month, day, count)

    @timeit
    def run_task(self):
        logger.info("extracting %s ", self.input_filename)
        # this pattern matches last occurence of 8 consecutive digits
        # e.g. 'LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv'
        # will match 20161110
        date_pattern = r'.*_(\d\d\d\d\d\d\d\d)'
        date_match = re.match(date_pattern, self.input_filename)
        if date_match:
            date_part = date_match.groups()[-1]
            self.most_recent_data_date = datetime.strptime(date_part, "%Y%m%d")
            logger.debug("identified most_recent_data_date=%s", self.most_recent_data_date)
        else:
            raise Exception("couldn't find a date pattern in filename. filename should be \
                LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv or similar")

        count = 0
        statements = []
        something_new = False
        query = """
            INSERT into %s(
                siret,
                hiring_date,
                zipcode,
                contract_type,
                departement,
                contract_duration,
                iiann,
                tranche_age,
                handicap_label
                )
            values(%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)
        """ % settings.DPAE_TABLE
        imported_dpae = 0
        imported_dpae_distribution = {}
        not_imported_dpae = 0
        initial_most_recent_data_date = DpaeStatistics.get_most_recent_data_date()

        logger.info("will now extract all dpae with hiring_date between %s and %s",
                    initial_most_recent_data_date, self.most_recent_data_date)

        with import_util.get_reader(self.input_filename) as myfile:
            con, cur = import_util.create_cursor()
            header_line = myfile.readline().strip()
            if "siret" not in header_line:
                logger.debug(header_line)
                raise Exception("wrong header line")
            for line in myfile:
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
                    siret, hiring_date, zipcode, contract_type, departement, contract_duration, \
                    iiann, tranche_age, handicap_label = parse_dpae_line(line)
                except ValueError:
                    self.zipcode_errors += 1
                    continue
                except DepartementException:
                    self.zipcode_errors += 1
                    continue
                except InvalidRowException:
                    logger.info("invalid_row met at row: %i", count)
                    self.invalid_row_errors += 1
                    continue

                if hiring_date > initial_most_recent_data_date and hiring_date <= self.most_recent_data_date:
                    statement = (
                        siret,
                        hiring_date,
                        zipcode,
                        contract_type,
                        departement,
                        contract_duration,
                        iiann,
                        tranche_age,
                        handicap_label
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
        if self.zipcode_errors >= 100:
            raise Exception('too many zipcode errors')
        if self.invalid_row_errors >= 100:
            raise Exception('too many invalid_row errors')
        statistics = DpaeStatistics(last_import=datetime.now(), most_recent_data_date=self.most_recent_data_date)
        statistics.save()
        con.commit()
        logger.info("finished importing dpae...")
        return something_new


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('main')
    if get_current_env() == ENV_LBBDEV:
        dpae_filename = sys.argv[1]
    else:
        with open(import_util.JENKINS_DPAE_PROPERTIES_FILENAME, "r") as f:
            dpae_filename = f.read().strip().split('=')[1]
    task = DpaeExtractJob(dpae_filename)
    task.run()
