import os
import unittest

from labonneboite.common.database import db_session, delete_db, engine, init_db
from labonneboite.importer.jobs.common import logger


class DatabaseTest(unittest.TestCase):
    """
    User and db need to be created before using this class.
    User DB_USER with password DB_PASSWORD need to have all privileges on DB_NAME.
    """

    def setUp(self):

        # pylint:disable=unused-variable
        # Imports are used by SQLAlchemy to know what tables to create.
        from labonneboite.importer.models.computing import Hiring, DpaeStatistics, ImportTask

        # pylint:enable=unused-variable

        db_session.remove()
        engine.dispose()
        delete_db()
        init_db()

        # Mute jobs logger
        logger.setLevel("CRITICAL")

        return super(DatabaseTest, self).setUp()

    def get_data_file_path(self, file_name):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", file_name))
