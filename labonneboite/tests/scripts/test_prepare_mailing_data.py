from labonneboite.common.models import Office
from labonneboite.scripts import prepare_mailing_data as script
from labonneboite.tests.test_base import DatabaseTest


class PrepareMailingDataBaseTest(DatabaseTest):
    """
    Create Elasticsearch and DB content for the unit tests.
    """

    def setUp(self, *args, **kwargs):
        super(PrepareMailingDataBaseTest, self).setUp(*args, **kwargs)

        # We should have 0 offices in the DB.
        self.assertEqual(Office.query.count(), 0)


class MinimalisticTest(PrepareMailingDataBaseTest):
    """
    Test prepare_mailing_data script.
    This test is quite minimalistic as there is no office in DB (nor in ES).
    """

    def test_prepare_mailing_data(self):
        script.prepare_mailing_data()
