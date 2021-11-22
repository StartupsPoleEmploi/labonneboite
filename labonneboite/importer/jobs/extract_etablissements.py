from urllib.parse import urlparse
import pandas as pd
import validators
import os

from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.importer.util import history_importer_job_decorator
from labonneboite.common.util import timeit
from labonneboite.importer.models.computing import ImportTask
from labonneboite.importer.models.computing import RawOffice
from labonneboite.common import departements as dpt
from labonneboite.common import encoding as encoding_util
from labonneboite.common import siret as siret_util
from labonneboite.common.database import db_session
from labonneboite.common.chunks import chunks
from labonneboite.importer.jobs.base import Job
from labonneboite.importer.jobs.common import logger
from labonneboite.common.load_data import load_effectif_labels
from labonneboite.common.env import get_current_env, ENV_TEST

# This list contains siret that must not be found in data,
# we use it as a test : if one of those is found in data, we stop the importer
# and need to extract data again
WRONG_SIRETS = ['50468025700020', #siret of Oxynel : old siret which has been replaced with this one : 50468025700038
                '48791579500024', #old siret for "L’entreprise Philippe Murielle a changé de SIRET en avril 2018 suite à un changement d’adresse"
                '41006536100041', #old siret for equant france sa - cesson sevigne
]

DF_EFFECTIF_TO_LABEL = load_effectif_labels()

class WrongSiretException(Exception):
    pass

def has_text_content(s):
    return s is not None and len(s) > 0 and not s.isspace()

def merge_and_normalize_websites(websites):
    for website in websites:
        clean_website = normalize_website_url(website)
        if clean_website:
            return clean_website
    return ""

def normalize_website_url(url):
    """
    website URLs are raw data entered by human, with lots of mistakes,
    so it has to be automatically cleaned up and normalized
    """
    if (not url) or ('@' in url) or ('.' not in url) or (len(url) <= 3):
        return None

    url = encoding_util.strip_french_accents(url)

    url = url.replace('"', '').strip()

    # add missing http prefix if needed
    if not urlparse(url).scheme:
        url = "http://" + url

    # normalization
    try:
        url = urlparse(url).geturl()
    except ValueError:
        return None

    # ensure website URL is correct (and is not an email address for example!)
    if not validators.url(url):
        return None

    return url



@timeit
def check_departements(departements):
    for dep in departements:
        con, cur = import_util.create_cursor()
        cur.execute("select count(1) from %s where departement='%s'" % (settings.RAW_OFFICE_TABLE, dep))
        con.commit()
        count = cur.fetchone()[0]
        if count < 1000:
            logger.error("only %s results for departement %s", count, dep)
        cur.close()
        con.close()


class EtablissementExtractJob(Job):
    file_type = "etablissements"
    import_type = ImportTask.ETABLISSEMENT
    table_name = settings.RAW_OFFICE_TABLE

    def __init__(self, etablissement_filename):
        self.input_filename = etablissement_filename

    @timeit
    def after_check(self):
        query = db_session.query(RawOffice.departement.distinct().label("departement"))
        departements = [row.departement for row in query.all()]

        if len(departements) != settings.DISTINCT_DEPARTEMENTS_HAVING_OFFICES:
            msg = "wrong number of departements : %s instead of expected %s" % (
                len(departements),
                settings.DISTINCT_DEPARTEMENTS_HAVING_OFFICES
            )
            raise Exception(msg)

        # FIXME parallelize for better performance
        for departement in departements:
            count = RawOffice.query.filter_by(departement=departement).count()
            logger.info("number of companies in departement %s : %i", departement, count)
            if not count >= settings.MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT:
                msg = "too few companies in departement : %s instead of expected %s" % (
                    count,
                    settings.MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT
                )
                raise Exception(msg)

    @timeit
    def run_task(self):
        # the strategy used here consumes way too much RAM (20G+)
        # because it needs the whole CSV dataset in memory
        # FIXME improve this by processing the CSV on-the-fly instead
        self.benchmark_loading_using_pandas()
        self.existing_sirets = self.get_sirets_from_database()
        num_created = 0
        sirets_inserted = set()
        existing_set = set(self.existing_sirets)

        for offices in self.get_offices_from_file():
            self.csv_offices = offices
            self.csv_sirets = list(self.csv_offices.keys())
            csv_set = set(self.csv_sirets)

            # 1 - create offices which did not exist before
            self.creatable_sirets = csv_set
            num_created += len(self.creatable_sirets)

            logger.info("nombre d'etablissement dans le csv : %i" % len(csv_set))

            i = 0
            logger.info("liste de 20 sirets dans le csv" )
            if csv_set :
                while  i < 20 :
                    i=i+1
                    value_test = csv_set.pop()
                    csv_set.add(value_test)
                    logger.info(" siret : %s" % value_test )


            logger.info("nombre d'etablissement existant : %i" % len(existing_set))

            i = 0
            logger.info("liste de 20 sirets existant" )
            if existing_set :
                while  i < 20 :
                    i=i+1
                    value_test = existing_set.pop()
                    existing_set.add(value_test)
                    logger.info(" siret : %s" % value_test )


            logger.info("nombre d'etablissement à créer : %i" % len(self.creatable_sirets))

            i = 0
            logger.info("liste de 20 sirets à créer" )
            if self.creatable_sirets :
                while  i < 20 :
                    i=i+1
                    value_test = self.creatable_sirets.pop()
                    self.creatable_sirets.add(value_test)
                    logger.info(" siret : %s" % value_test )

            self.create_update_offices()
            sirets_inserted = sirets_inserted.union(csv_set)
        # 2 - delete offices which no longer exist
        self.deletable_sirets = existing_set - sirets_inserted
        self.delete_deletable_offices()
        return num_created

    @timeit
    def get_sirets_from_database(self):
        query = "select siret from %s" % settings.RAW_OFFICE_TABLE
        logger.info("get offices from database")
        con, cur = import_util.create_cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        con.close()
        return [row[0] for row in rows if siret_util.is_siret(row[0])]

    @timeit
    def update_updatable_offices(self):
        # FIXME parallelize and/or batch for better performance
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
            website=%%s,
            flag_poe_afpr=%%s,
            flag_pmsmp=%%s
        where siret=%%s""" % settings.RAW_OFFICE_TABLE

        count = 0
        logger.info("update updatable offices in table %s", settings.RAW_OFFICE_TABLE)
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
                if not count % 100000:
                    logger.info("updated %s offices", count)
        if statements:
            cur.executemany(query, statements)
            con.commit()
        cur.close()
        con.close()
        logger.info("%i offices updated.", count)

    @timeit
    def create_update_offices(self):
        """
        create new offices (that are not yet in our etablissement table)
        """
        con, cur = import_util.create_cursor()
        query = """INSERT into %s(siret, raisonsociale, enseigne, codenaf, numerorue,
            libellerue, codecommune, codepostal, email, tel, departement, trancheeffectif,
            website, flag_poe_afpr, flag_pmsmp)
        values(%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)
        ON DUPLICATE KEY UPDATE
            raisonsociale=VALUES(raisonsociale),
            enseigne=VALUES(enseigne),
            codenaf=VALUES(codenaf),
            numerorue=VALUES(numerorue),
            libellerue=VALUES(libellerue),
            codecommune=VALUES(codecommune),
            codepostal=VALUES(codepostal),
            email=VALUES(email),
            tel=VALUES(tel),
            departement=VALUES(departement),
            trancheeffectif=VALUES(trancheeffectif),
            website=VALUES(website),
            flag_poe_afpr=VALUES(flag_poe_afpr),
            flag_pmsmp=VALUES(flag_pmsmp)""" % settings.RAW_OFFICE_TABLE

        count = 1
        logger.info("create new offices in table %s", settings.RAW_OFFICE_TABLE)
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
                if not count % 10000:
                    logger.info("created %s offices", count)
        if statements:
            cur.executemany(query, statements)
            con.commit()
        cur.close()
        con.close()
        logger.info("%i new offices created.", count)

    @timeit
    def delete_deletable_offices(self):
        con, cur = import_util.create_cursor()
        if self.deletable_sirets:
            for sirets in chunks(list(self.deletable_sirets), 500):
                stringified_siret_list = ",".join(sirets)
                logger.info("deleting a chunk of %i offices...", len(sirets))
                query = """DELETE FROM %s where siret IN (%s)""" % (settings.RAW_OFFICE_TABLE, stringified_siret_list)
                try:
                    cur.execute(query)
                    con.commit()
                except:
                    logger.warning("error while deleting chunk of sirets : %s", sirets)
                    raise
        cur.close()
        con.close()
        logger.info("%i no longer existing offices deleted.", len(self.deletable_sirets))

    @timeit
    def benchmark_loading_using_pandas(self):
        return  # not working yet, see below
        
        # FIXME retry this very soon, as soon as we have the pipe delimiter

        # ValueError: Falling back to the 'python' engine because the separator encoded in UTF-8 is > 1 char long,
        # and the 'c' engine does not support such separators, but this causes 'error_bad_lines' to be ignored as
        # it is not supported by the 'python' engine.
        df = pd.read_csv(
            self.input_filename,
            sep='\xa5',
            error_bad_lines=False,  # no longer raise Exception when a row is incorrect (wrong number of fields...)
            warn_bad_lines=True,  # still display warning about those ignored incorrect rows
        )


    @timeit
    def get_offices_from_file(self):
        # FIXME elegantly parallelize this stuff
        # see
        # https://stackoverflow.com/questions/8717179/chunking-data-from-a-large-file-for-multiprocessing
        # https://docs.python.org/2/library/itertools.html#itertools.islice
        logger.info("extracting %s...", self.input_filename)
        departements = dpt.DEPARTEMENTS
        count = 0
        no_zipcode_count = 0
        unprocessable_departement_errors = 0
        format_errors = 0
        # KPI expected after the add of the RGPD email column
        emails_here_before_rgpd = 0 # Number of offices who did not have email before, and now have one
        emails_not_here_before_rgpd = 0 # Number of offices who had an existing email, which has been replaced by the new rgpd mail clean
        departement_counter_dic = {}
        offices = {}


        with import_util.get_reader(self.input_filename) as myfile:
            header_line = myfile.readline().strip()  # FIXME detect column positions from header
            if b"siret" not in header_line:
                logger.debug(header_line)
                raise ValueError("wrong header line")
            for line in myfile:
                line = line.decode()
                count += 1


                try:
                    fields = import_util.get_fields_from_csv_line(line)

                    if len(fields) != 22:
                        logger.exception("wrong number of fields in line %s", line)
                        raise ValueError

                    siret, raisonsociale, enseigne, codenaf, numerorue, \
                        libellerue, codecommune, codepostal, email, \
                        tel, trancheeffectif_etablissement, effectif_reel, _, _, \
                        website1, website2, better_tel, \
                        website3, _, contrat_afpr, contrat_poe, contrat_pmsmp = fields

                    if not siret_util.is_siret(siret):
                        logger.exception("wrong siret : %s", siret)
                        raise ValueError

                    if siret in WRONG_SIRETS:
                        logger.exception("wrong siret : %s, should not be here - need other extract from datalake", siret)
                        raise WrongSiretException

                except ValueError:
                    logger.exception("exception in line %s", line)
                    format_errors += 1
                    continue

                # We cant rely on the field trancheeffectif_etablissement which is in etablissement file
                # We have to rely on the field effectif_reel
                # We take the number of employees and we use a dataframe which will help us to determine which category the number of employees is related to 
                # If there is no effectif reel in the dataset OR it is 0, we use the old field tranche_effectif
                if effectif_reel != '':
                    if int(effectif_reel) > 0:
                        trancheeffectif_etablissement = DF_EFFECTIF_TO_LABEL[ 
                            (DF_EFFECTIF_TO_LABEL.start_effectif <= int(effectif_reel)) & 
                            (DF_EFFECTIF_TO_LABEL.end_effectif >= int(effectif_reel))
                        ]['code'].values[0]

                website = merge_and_normalize_websites([website1, website2, website3])

                if has_text_content(better_tel):
                    tel = better_tel
                flag_pmsmp = 0
                if contrat_pmsmp == "O":
                    flag_pmsmp = 1

                flag_poe_afpr = 0
                if contrat_poe == "O" or contrat_afpr == "O":
                    flag_poe_afpr = 1

                if codecommune.strip():
                    departement = import_util.get_departement_from_zipcode(codepostal)
                    process_this_departement = departement in departements
                    if process_this_departement:
                        # Trello Pz5UlnFh : supprimer-les-emails-pe-des-entreprises-qui-ne-sont-pas-des-agences-pe
                        if  "@pole-emploi." in email and raisonsociale != "POLE EMPLOI":
                            email = ""
                        if len(codepostal) == 4:
                            codepostal = "0%s" % codepostal
                        etab_create_fields = siret, raisonsociale, enseigne, codenaf, numerorue, libellerue, \
                            codecommune, codepostal, email, tel, departement, trancheeffectif_etablissement, \
                            website, flag_poe_afpr, flag_pmsmp
                        etab_update_fields = raisonsociale, enseigne, codenaf, numerorue, libellerue, \
                            codecommune, codepostal, email, tel, departement, trancheeffectif_etablissement, \
                            website, flag_poe_afpr, flag_pmsmp, siret
                        if codepostal.startswith(departement):
                            departement_counter_dic.setdefault(departement, 0)
                            departement_counter_dic[departement] += 1
                            offices[siret] = {
                                "create_fields": etab_create_fields,
                                "update_fields": etab_update_fields,
                            }
                        else:
                            logger.info(
                                "zipcode %s and departement %s don't match commune_id %s",
                                codepostal,
                                departement,
                                codecommune,
                            )
                    else:
                        unprocessable_departement_errors += 1
                else:
                    no_zipcode_count += 1
                if not count % 100000:
                    logger.debug("processed %s lines", count)
                    yield offices
                    offices = {}

        logger.info("%i offices total", count)
        logger.info("%i offices without email before and have now thanks to RGPD mails", emails_not_here_before_rgpd)
        logger.info("%i offices with emails before and have been replaced by RGPD mails", emails_here_before_rgpd)
        logger.info("%i offices with unprocessable departement", unprocessable_departement_errors)
        logger.info("%i offices with no zipcodes", no_zipcode_count)
        logger.info("%i offices not read because of format error", format_errors)
        logger.info("%i distinct departements from file", len(departement_counter_dic))
        departement_count = sorted(departement_counter_dic.items())
        logger.info("per departement read %s", departement_count)
        logger.info("finished reading offices...")

        if get_current_env() != ENV_TEST:
            if unprocessable_departement_errors > 2500:
                raise ValueError("too many unprocessable_departement_errors")
            if no_zipcode_count > 75000:
                raise ValueError(f"too many no_zipcode_count: {no_zipcode_count}")
            if format_errors > 5:
                raise ValueError("too many format_errors")
            if len(departement_counter_dic) != settings.DISTINCT_DEPARTEMENTS_HAVING_OFFICES:
                msg = "incorrect total number of departements : %s instead of expected %s" % (
                    len(departement_counter_dic),
                    settings.DISTINCT_DEPARTEMENTS_HAVING_OFFICES
                )
                raise ValueError(msg)
            for departement, count in departement_count:
                if not count >= settings.MINIMUM_OFFICES_TO_BE_EXTRACTED_PER_DEPARTEMENT:
                    logger.exception("only %s offices in departement %s", count, departement)
                    raise ValueError("not enough offices in at least one departement")

        yield offices

@history_importer_job_decorator(os.path.basename(__file__))
def run():
    etablissement_filename = import_util.detect_runnable_file("etablissements")
    task = EtablissementExtractJob(etablissement_filename)
    task.run()

if __name__ == "__main__":
    run()

