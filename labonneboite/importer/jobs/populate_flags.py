import os
import tarfile

from labonneboite.importer import util as import_util
from labonneboite.importer import settings
from .base import Job
from .common import logger


def populate_flags():
    logger.info("going to populate office boolean flags...")
    for flag in import_util.OFFICE_FLAGS:
        populate_flag(flag)
    logger.info("all flags populated!")


def populate_flag(flag):
    logger.info("populating %s ... ", flag)
    con, cur = import_util.create_cursor()
    query = """
        UPDATE
        %s e
        INNER JOIN %s f
        ON e.siret = f.siret
        SET e.%s = True;
    """ % (settings.EXPORT_ETABLISSEMENT_TABLE, flag, flag)
    cur.execute(query)
    con.commit()
    logger.info("completed populating %s ... ", flag)


def run_sql_script(sql_script):
    con, cur = import_util.create_cursor()

    for query in sql_script.split(';'):
        query = query.strip()
        if len(query) >= 1:
            cur.execute(query)
            con.commit()


def prepare_flags_junior_and_senior():
    logger.info("preparing flags_junior_and_senior...")

    sql_script = """
        drop table if exists flag_tmp1;
        create table flag_tmp1 as
        (
        select
        siret,
        tranche_age,
        count(*) as contrats
        from
        dpae
        where (contract_type=2) or (contract_type=1 and contract_duration > 31)
        group by
        siret,
        tranche_age
        );

        drop table if exists flag_tmp2;
        create table flag_tmp2
        as
        (
        select
            siret,
            100*sum(contrats*(tranche_age='00-25'))/sum(contrats) as ratio_junior,
            100*sum(contrats*(tranche_age='51-99'))/sum(contrats) as ratio_senior
        from flag_tmp1
        group by siret
        );

        drop table if exists flag_junior;
        create table flag_junior
        as
        (
        select
            siret
        from flag_tmp2
        where ratio_junior >= 80
        );

        drop table if exists flag_senior;
        create table flag_senior
        as
        (
        select
            siret
        from flag_tmp2
        where ratio_senior >= 16
        );

        drop table if exists flag_tmp1;
        drop table if exists flag_tmp2;
    """

    run_sql_script(sql_script)
    logger.info("completed preparing flags_junior_and_senior.")

def prepare_flag_handicap():
    logger.info("preparing flag_handicap...")

    sql_script = """
        drop table if exists flag_handicap;
        create table flag_handicap as
        (
        select distinct(siret) from dpae
        where
            (
                (contract_type=2) or (contract_type=1 and contract_duration > 31)
            )
            and
            ( handicap_label = 'RQTH-MDT' )
        );
    """

    run_sql_script(sql_script)
    logger.info("completed preparing flag_handicap.")

def dump():
    timestamp = settings.NOW.strftime('%Y_%m_%d_%H%M')

    copy_to_remote_server = Job().backup_first
    logger.info("backing up export_etablissement")
    etab_result = import_util.back_up(
        settings.BACKUP_OUTPUT_FOLDER, settings.EXPORT_ETABLISSEMENT_TABLE,
        "export_etablissement", timestamp, copy_to_remote_server,
        rename_table=True)

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
        pass
    # this is a hard link, not a symlink
    os.link(archive_path, link_path)


if __name__ == "__main__":
    # FIXME restore those
    # prepare_flags_junior_and_senior()
    # prepare_flag_handicap()
    # populate_flags()
    filename = dump()
    make_link_file_to_new_archive(filename)
