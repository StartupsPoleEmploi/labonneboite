import argparse

from labonneboite.importer import util as import_util
from labonneboite.importer.jobs.common import logger

def remove_hiring_until_date(floor_date):
    logger.info("deleting hiring to %s... ", floor_date)
    con, cur = import_util.create_cursor()
    query = """
        DELETE FROM hiring where date_insertion > "%s"
    """ % floor_date
    cur.execute(query)
    con.commit()
    logger.info("completed populating %s ... ", flag)
    cur.close()
    con.close()

def run():
    parser = argparse.ArgumentParser(description="""Removing hiring based to floor date input""")
    parser.add_argument("-d", "--date", type=str, default="0000-00-00")
    args = parser.parse_args()
    remove_hiring_until_date(args.date)

if __name__ == "__main__":
    run()