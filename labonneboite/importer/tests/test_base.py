import os
import unittest

from labonneboite.common.database import db_session, init_db, delete_db, engine

from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger

importer_settings.INPUT_SOURCE_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
importer_settings.MIN_DPAE_COUNT_PER_DAY = 0
importer_settings.OFFICE_TABLE = 'etablissements'
importer_settings.SCORE_COEFFICIENT_OF_VARIATION_MAX = 1.0


class DatabaseTest(unittest.TestCase):
    """
    User and db need to be created before using this class.
    User 'lbb_test' with password 'lbb_test' need to have all privileges on db 'lbb_test2'.
    """

    def setUp(self):

        # pylint:disable=unused-variable
        # Imports are used by SQLAlchemy to know what tables to create.
        from labonneboite.importer.models.computing import Dpae, DpaeStatistics, ImportTask
        # pylint:enable=unused-variable

        db_session.remove()
        engine.dispose()
        delete_db()
        init_db()

        # Mute jobs logger
        logger.setLevel('CRITICAL')


        return super(DatabaseTest, self).setUp()

    def get_data_file_path(self, file_name):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", file_name))
