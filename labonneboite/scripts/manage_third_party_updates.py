#!/usr/bin/python
"""
    This script manages data from the `etablissements_third_party_update` table. This lets us do experiments, like the one with CBS school in 2021. Each experiment can have a key, stored in the `reason` field of the DB, which is used to get and remove the records corresponding to the given experiment.
    usage:
        ENABLE_DB_INFILE=1 python labonneboite/scripts/cbs_to_save.py [command] [option] [csv path]
    Command: insert, delete, count
    Options: key
    Path: for insert, path of the CSV file
    When using insert you can provide the path to the CSV file (defaults to labonneboite/common/data/cbs_data_test.csv), e.g. `ENABLE_DB_INFILE=1 python labonneboite/scripts/cbs_to_save.py insert ../tirage_LBA_170621.csv`
    Note: when running the script locally it requires the `LBB_ENV=development` env var
    Note: apply in production
    ```
    $ ssh lbbprod1
    $ docker exec -it labonneboite_labonneboite_1 bash
    # python labonneboite/scripts/cbs_to_save.py delete
    # source /labonneboite/env/bin/activate
    # ENABLE_DB_INFILE=1 python labonneboite/scripts/cbs_to_save.py insert ../tirage_LBA_170621.csv
    ```
"""
import sys
import os
import time
import argparse
from sqlalchemy import text
from labonneboite.common.database import db_session, engine

parser = argparse.ArgumentParser(description='Manage third party updates')
parser.add_argument('command', metavar='command', type=str, help='insert, delete or count')
parser.add_argument('path', metavar='path', type=str, help='path to the CSV file to import', nargs='?')
parser.add_argument('--key', dest='key', help='the key of this experiment')

args = parser.parse_args()
print(args)

REASON_KEY = args.key or 'cbs_xp'
command = args.command
file = args.path or 'labonneboite/common/data/cbs_data_test.csv'

def cbs_count_records():
    sql = text("""
        SELECT COUNT(*) FROM labonneboite.etablissements_third_party_update where reason='%s';
    """ % (REASON_KEY))
    try:
        res = db_session.execute(sql)
        print('> CBS records count: ', res.first()[0])
    except Exception as err:
        print('> error executing request', err)

def cbs_delete_records():
    try:
        print('> Deleting CBS records...')
        sql = text("""
            delete from labonneboite.etablissements_third_party_update where reason='%s';
        """ % (REASON_KEY))
        db_session.execute(sql)
        db_session.commit()
        print('> Done')
    except Exception as err:
        print('> error executing request', err)

def cbs_insert_records():
    try:
        print('> Inserting CBS records...', file)
        sql = text("""
            LOAD DATA LOCAL INFILE '%s' into table etablissements_third_party_update FIELDS ENCLOSED BY '\"' TERMINATED BY ','  LINES TERMINATED BY '\\n' IGNORE 1 ROWS (@score,@siret) SET score_alternance=@score, sirets=@siret, reason='%s', date_created=NOW();
        """ % (file, REASON_KEY))
        db_session.execute(sql)
        db_session.commit()
        print('> Done')
    except Exception as err:
        print('> error executing request', err, '\n> Did you forget to set the env var `ENABLE_DB_INFILE=1`?')

def main():
    print('\nStarting script with LBB_ENV:', os.environ.get('LBB_ENV', None), 'and command:', command, 'and key:', REASON_KEY, '\n')

    if(command == 'count'): cbs_count_records()

    elif(command == 'delete'):
        cbs_count_records()
        cbs_delete_records()
        cbs_count_records()

    elif(command == 'insert'):
        cbs_count_records()
        cbs_insert_records()
        cbs_count_records()

    else: print('Unknown command', command)

if __name__ == "__main__":
    start_time = time.time()
    main()
    engine.dispose()
    print("--- %s seconds ---" % (time.time() - start_time))

