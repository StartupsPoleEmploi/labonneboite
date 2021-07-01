#!/usr/bin/python
"""
    This script manages data we add to the SAVE DB programatically as part of an experiment with CBS school
    usage:
        ENABLE_DB_INFILE=1 python labonneboite/scripts/cbs_to_save.py count
    Params: insert, delete, count
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
from sqlalchemy import text
from labonneboite.common.database import db_session, engine

REASON_KEY = 'cbs_xp'

def cbs_count_records():
    sql = text("""
        SELECT COUNT(*) FROM labonneboite.etablissements_admin_update where reason='%s';
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
            delete from labonneboite.etablissements_admin_update where reason='%s';
        """ % (REASON_KEY))
        db_session.execute(sql)
        db_session.commit()
        print('> Done')
    except Exception as err:
        print('> error executing request', err)

def cbs_insert_records():
    try:
        file = sys.argv[2] if len(sys.argv) > 2 else 'labonneboite/common/data/cbs_data_test.csv'
        print('> Inserting CBS records...', file)
        sql = text("""
            LOAD DATA LOCAL INFILE '%s' into table etablissements_admin_update FIELDS ENCLOSED BY '\"' TERMINATED BY ','  LINES TERMINATED BY '\\n' IGNORE 1 ROWS (@score,@siret) SET score_alternance=@score, sirets=@siret, reason='%s', date_created=NOW();
        """ % (file, REASON_KEY))
        db_session.execute(sql)
        db_session.commit()
        print('> Done')
    except Exception as err:
        print('> error executing request', err, '\n> Did you forget to set the env var `ENABLE_DB_INFILE=1`?')

def main():
    # os.environ['LBB_ENV'] = 'development'
    command = sys.argv[1]

    print('\nStarting script with LBB_ENV=', os.environ.get('LBB_ENV', None), ' and command:', command, '\n')

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

