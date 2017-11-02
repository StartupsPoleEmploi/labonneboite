"""
Extracts offices("etablissements").

To be done.
"""
import sys

from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.importer.models.computing import ImportTask
from labonneboite.common import encoding as encoding_util
from .base import Job
from .common import logger


class DepartementException(Exception):
    pass


def extract_departement_from_zipcode(zipcode, siret):
    zipcode = zipcode.strip()
    departement = None
    if len(zipcode) in range(1, 6):
        if len(zipcode) == 1:
            departement = "0%s" % zipcode[0]
        elif len(zipcode) == 2:
            departement = zipcode
        elif len(zipcode) == 4:
            departement = "0%s" % zipcode[0]
        elif len(zipcode) == 5:
            departement = zipcode[:2]
        else:
            raise DepartementException("length ok but departement not recognized for siret='%s' and zipcode='%s'" % (siret, zipcode))
    else:
        raise DepartementException("departement not recognized for siret='%s' and zipcode='%s'" % (siret, zipcode))
    if departement == "2A" or departement == "2B":
        departement = "20"
    return departement


def check_departements(departements):
    for dep in departements:
        con, cur = import_util.create_cursor()
        cur.execute("select count(1) from %s where departement='%s'" % (settings.OFFICE_TABLE, dep))
        con.commit()
        count = cur.fetchone()[0]
        if count < 1000:
            logger.error("only %s results for departement %s", count, dep)


class EtablissementExtractJob(Job):
    file_type = "etablissements"
    import_type = ImportTask.ETABLISSEMENT
    table_name = settings.OFFICE_TABLE

    def __init__(self, etablissement_filename):
        self.input_filename = etablissement_filename

    def after_check(self):
        _, cur = import_util.create_cursor()
        for departement in settings.DEPARTEMENTS:
            query = "select count(1) from %s where departement='%s'" % (
                settings.OFFICE_TABLE,
                departement)
            cur.execute(query)
            result = cur.fetchone()
            count = result[0]
            logger.info("number of companies in departement %s : %i", departement, count)
            if count <= 1000:
                raise "too few companies"

    def run_task(self):
        self.csv_offices = self.get_offices_from_file()
        self.csv_sirets = self.csv_offices.keys()
        self.existing_sirets = self.get_sirets_from_database()
        csv_set = set(self.csv_sirets)
        existing_set = set(self.existing_sirets)
        # 1 - create offices which did not exist before
        self.creatable_sirets = csv_set - existing_set
        num_created = self.create_creatable_offices()
        # 2 - delete offices which no longer exist
        self.deletable_sirets = existing_set - csv_set
        self.delete_deletable_offices()
        # 3 - update existing offices
        self.updatable_sirets = existing_set - self.deletable_sirets
        self.update_updatable_offices()
        return num_created

    def get_sirets_from_database(self):
        query = "select siret from %s where siret != ''" % settings.OFFICE_TABLE
        logger.info("get etablissements from database")
        _, cur = import_util.create_cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return [row[0] for row in rows]

    def update_updatable_offices(self):
        con, cur = import_util.create_cursor()
        query = """UPDATE %s SET
            raisonsociale=%%s,
            enseigne=%%s,
            codenaf=%%s,
            numerorue=%%s,
            libellerue=%%s,
            codecommune=%%s,
            codepostal=%%s,
            email=%%s,
            tel=%%s,
            departement=%%s,
            trancheeffectif=%%s,
            website1=%%s,
            website2=%%s
        where siret=%%s""" % settings.OFFICE_TABLE

        count = 1
        logger.info("update updatable etablissements in table %s", settings.OFFICE_TABLE)
        statements = []
        MAX_COUNT_EXECUTE = 500
        for siret in self.updatable_sirets:
            statement = self.csv_offices[siret]["update_fields"]
            statements.append(statement)
            count += 1
            if not count % MAX_COUNT_EXECUTE:
                cur.executemany(query, statements)
                con.commit()
                statements = []
        if statements:
            cur.executemany(query, statements)
            con.commit()
        logger.info("%i etablissements updated.", count)

    def create_creatable_offices(self):
        """
        create new etablissements (that are not yet in our etablissement table)
        """
        con, cur = import_util.create_cursor()
        query = """INSERT into %s(siret, raisonsociale, enseigne, codenaf, numerorue,
            libellerue, codecommune, codepostal, email, tel, departement, trancheeffectif,
            website1, website2)
        values(%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)""" % settings.OFFICE_TABLE

        count = 1
        logger.info("create new etablissements in table %s", settings.OFFICE_TABLE)
        statements = []
        MAX_COUNT_EXECUTE = 500
        for siret in self.creatable_sirets:
            statement = self.csv_offices[siret]["create_fields"]
            statements.append(statement)
            count += 1
            if not count % MAX_COUNT_EXECUTE:
                cur.executemany(query, statements)
                con.commit()
                statements = []
        if statements:
            cur.executemany(query, statements)
            con.commit()
        logger.info("%i new etablissements created.", count)

    def delete_deletable_offices(self):
        con, cur = import_util.create_cursor()
        if self.deletable_sirets:
            stringified_siret_list = ",".join(self.deletable_sirets)
            logger.info("going to delete %i offices...", len(self.deletable_sirets))
            query = """DELETE FROM %s where siret IN (%s)""" % (settings.OFFICE_TABLE, stringified_siret_list)
            try:
                cur.execute(query)
                con.commit()
            except:
                logger.warning("deletable_sirets=%s", self.deletable_sirets)
                raise
            logger.info("%i old offices deleted.", len(self.deletable_sirets))

    def get_offices_from_file(self):
        logger.info("extracting %s...", self.input_filename)
        departements = settings.DEPARTEMENTS
        count = 0
        no_zipcode_count = 0
        departement_errors = 0
        unprocessable_departement_errors = 0
        format_errors = 0
        _, _ = import_util.create_cursor()
        departement_counter_dic = {}
        etablissements = {}

        with import_util.get_reader(self.input_filename) as myfile:
            header_line = myfile.readline().strip()
            if "siret" not in header_line:
                logger.debug(header_line)
                raise "wrong header line"
            for line in myfile:
                count += 1
                if not count % 100000:
                    logger.debug("reading line %i", count)

                try:
                    fields = import_util.get_fields_from_csv_line(line)
                    if len(fields) != 16:
                        logger.exception("wrong number of fields in line %s", line)
                        raise ValueError

                    siret, raisonsociale, enseigne, codenaf, numerorue, \
                        libellerue, codecommune, codepostal, email, tel, \
                        trancheeffectif_etablissement, _, _, _, \
                        website1, website2 = fields
                except ValueError:
                    logger.exception("exception in line %s", line)
                    format_errors += 1
                    continue

                website1 = encoding_util.strip_french_accents(website1)
                website2 = encoding_util.strip_french_accents(website2)
                email = encoding_util.strip_french_accents(email)

                if codecommune.strip():
                    try:
                        departement = extract_departement_from_zipcode(codepostal, siret)
                        process_this_departement = departement in departements
                        if process_this_departement:

                            if len(codepostal) == 4:
                                codepostal = "0%s" % codepostal
                            etab_create_fields = siret, raisonsociale, enseigne, codenaf, numerorue, libellerue, \
                                codecommune, codepostal, email, tel, departement, trancheeffectif_etablissement, \
                                website1, website2
                            etab_update_fields = raisonsociale, enseigne, codenaf, numerorue, libellerue, \
                                codecommune, codepostal, email, tel, departement, trancheeffectif_etablissement, \
                                website1, website2, siret
                            if codepostal.startswith(departement):
                                departement_counter_dic.setdefault(departement, 0)
                                departement_counter_dic[departement] += 1
                                etablissements[siret] = {
                                    "create_fields": etab_create_fields,
                                    "update_fields": etab_update_fields,
                                }
                            else:
                                logger.info("zipcode and departement dont match code commune: %s, code postal: %s, departement: %s", codecommune, codepostal, departement)
                        else:
                            unprocessable_departement_errors += 1
                    except DepartementException:
                        logger.exception("departement exception")
                        departement_errors += 1
                else:
                    no_zipcode_count += 1

        logger.info("%i etablissements total", count)
        logger.info("%i etablissements with incorrect departement", departement_errors)
        logger.info("%i etablissements with unprocessable departement", unprocessable_departement_errors)
        logger.info("%i etablissements with no zipcodes", no_zipcode_count)
        logger.info("%i etablissements not read because of format error", format_errors)
        logger.info("%i number of departements from file", len(departement_counter_dic))
        departement_count = sorted(departement_counter_dic.items())
        logger.info("per departement read %s", departement_count)
        logger.info("finished reading etablissements...")

        if departement_errors > 500:
            raise "too many departement_errors"
        if unprocessable_departement_errors > 2000:
            raise "too many unprocessable_departement_errors"
        if no_zipcode_count > 40000:
            raise "too many no_zipcode_count"
        if format_errors > 5:
            raise "too many format_errors"
        if len(departement_counter_dic) not in [96, 15]:  # 96 in production, 15 in test
            logger.exception("incorrect total number of departements : %s", len(departement_counter_dic))
            raise "incorrect total number of departements"
        if len(departement_counter_dic) == 96:
            for departement, count in departement_count:
                if count < 10000:
                    logger.exception("only %s etablissements in departement %s", count, departement)
                    raise "not enough etablissements in at least one departement"

        return etablissements


if __name__ == "__main__":
    etablissement_filename = sys.argv[1]
    task = EtablissementExtractJob(etablissement_filename)
    task.run()
