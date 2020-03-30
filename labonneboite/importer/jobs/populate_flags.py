import os
import tarfile
from datetime import datetime
from shutil import copyfile

from labonneboite.importer import util as import_util
from labonneboite.importer.util import history_importer_job_decorator
from labonneboite.common.util import timeit
from labonneboite.importer import settings
from labonneboite.importer.jobs.common import logger


@timeit
def populate_flags():
    logger.info("going to populate office boolean flags...")
    for flag in import_util.OFFICE_FLAGS:
        populate_flag(flag)
    logger.info("all flags populated!")


@timeit
def populate_flag(flag):
    logger.info("populating %s ... ", flag)
    con, cur = import_util.create_cursor()
    query = """
        UPDATE
        %s e
        INNER JOIN %s f
        ON e.siret = f.siret
        SET e.%s = True;
    """ % (settings.SCORE_REDUCING_TARGET_TABLE, flag, flag)
    cur.execute(query)
    con.commit()
    logger.info("completed populating %s ... ", flag)
    cur.close()
    con.close()



@timeit
def prepare_flags_junior_and_senior():
    logger.info("preparing flags_junior_and_senior...")

    sql_script = """
        drop table if exists flag_tmp1;
        create table flag_tmp1 as
        (
        select siret, tranche_age, count(*) as contrats
        from %s
        where hiring_date >= DATE_SUB(NOW(),INTERVAL 1 YEAR)
        group by siret, tranche_age
        );

        drop table if exists flag_tmp2;
        create table flag_tmp2 as
        (
        select
            siret,
            100*sum(contrats*(tranche_age='00-25'))/sum(contrats) as ratio_junior,
            100*sum(contrats*(tranche_age='51-99'))/sum(contrats) as ratio_senior
        from flag_tmp1
        group by siret
        );

        drop table if exists flag_junior;
        create table flag_junior as
        (
        select siret
        from flag_tmp2
        where ratio_junior >= 80
        );

        drop table if exists flag_senior;
        create table flag_senior as
        (
        select siret
        from flag_tmp2
        where ratio_senior >= 16
        );

        drop table if exists flag_tmp1;
        drop table if exists flag_tmp2;
    """ % settings.HIRING_TABLE

    import_util.run_sql_script(sql_script)
    logger.info("completed preparing flags_junior_and_senior.")


@timeit
def prepare_flag_handicap():
    logger.info("preparing flag_handicap...")

    sql_script = """
        drop table if exists flag_handicap;
        create table flag_handicap as
        (
        select distinct(siret) from %s
        where
            handicap_label = 'RQTH-MDT'
            and hiring_date >= DATE_SUB(NOW(),INTERVAL 1 YEAR)
        );
    """ % settings.HIRING_TABLE

    import_util.run_sql_script(sql_script)
    logger.info("completed preparing flag_handicap.")


@timeit
def dump():
    timestamp = datetime.now().strftime('%Y_%m_%d_%H%M')

    logger.info("backing up table %s ...", settings.SCORE_REDUCING_TARGET_TABLE)
    etab_result = import_util.back_up(
        settings.BACKUP_OUTPUT_FOLDER, settings.SCORE_REDUCING_TARGET_TABLE,
        "export_etablissement", timestamp, new_table_name="etablissements_new")

    tar_filename = os.path.join(settings.BACKUP_FOLDER, "%s.tar.bz2" % timestamp)
    with tarfile.open(tar_filename, "w:bz2") as tar:
        logger.info("creating tar file %s...", tar_filename)
        tar.add(etab_result, arcname=os.path.basename(etab_result))
        tar.close()
    return tar_filename


def make_link_file_to_new_archive(archive_path):
    link_path = os.path.join(settings.BACKUP_FOLDER, "latest_data.tar.bz2")

    try:
        os.remove(link_path)
    except OSError:
        pass  # link_path did not already exist
    
    try:
        # this is a hard link, not a symlink
        # hard linking fails on Vagrant, error seems to be known:
        # https://github.com/pypa/setuptools/issues/516
        os.link(archive_path, link_path)
    except OSError:
        copyfile(archive_path, link_path)

@history_importer_job_decorator(job_name=os.path.basename(__file__))
def run_main():
    prepare_flags_junior_and_senior()
    prepare_flag_handicap()
    populate_flags()
    filename = dump()
    make_link_file_to_new_archive(filename)

if __name__ == "__main__":
    run_main
