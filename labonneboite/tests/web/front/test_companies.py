import unittest.mock
import pytest
from labonneboite.common.models import Office
from labonneboite.common import pdf
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common.load_data import load_groupements_employeurs


class DownloadTest(DatabaseTest):

    # replace setup by a pytest fixture
    # sytt: https://github.com/pytest-dev/pytest-mock/issues/174
    @pytest.fixture(autouse=True)
    def _test_data(self):
        # Create an office.
        self.office = Office(
            departement='75',
            siret='78548035101646',
            company_name='NICOLAS',
            headcount='03',
            city_code='75110',
            zipcode='75010',
            naf='4646Z',
            tel='0100000000',
            hiring=100,  # aka: score 80
            x=2.3488,
            y=48.8534,
        )
        self.db_session.add(self.office)
        self.db_session.commit()

        # Remove pdf file if it already exists
        pdf.delete_file(self.office)

    def setUp(self):
        super().setUp()

    def test_office_fields_and_properties_are_str(self):
        """
        Check if office fields are str
        """

        self.assertEqual(type(self.office.company_name), str)
        self.assertEqual(type(self.office.address_as_text), str)
        self.assertEqual(type(self.office.phone), str)
        self.assertEqual(type(self.office.google_url), str)

    def test_office_details_page(self):
        """
        Test the office details page of a regular office.
        """

        rv = self.app.get(self.url_for('office.details', siret=self.office.siret))
        self.assertEqual(rv.status_code, 200)

    def test_office_details_page_of_non_existing_office(self):
        """
        Test the office details page of a non existing office.
        """

        # The details page of an nonexistent office should raise a 404.
        rv = self.app.get(self.url_for('office.details', siret='7x5x8x3x1x1x46'))
        self.assertEqual(rv.status_code, 404)

    def test_office_details_page_of_office_having_buggy_naf(self):
        """
        Test the office details page of an office having NAF 9900Z.
        """

        self.db_session.query(Office).filter(Office.siret == self.office.siret).\
            update({"naf": "9900Z"}, synchronize_session="fetch")

        rv = self.app.get(self.url_for('office.details', siret=self.office.siret))
        self.assertEqual(rv.status_code, 200)

    def test_office_details_page_of_office_which_is_a_groupement_employeurs(self):
        """
        Test the office details page of an office being a groupement d'employeurs.
        """
        self.db_session.query(Office).filter(Office.siret == self.office.siret).\
            update({"siret": "30651644400024"}, synchronize_session="fetch")

        self.assertIn(self.office.siret, load_groupements_employeurs())

        rv = self.app.get(self.url_for('office.details', siret=self.office.siret))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(
            u"Cette entreprise est un groupement d'employeurs.",
            rv.data.decode(),
        )

    def test_office_details_page_of_office_which_is_not_a_groupement_employeurs(self):
        """
        Test the office details page of an office not being a groupement d'employeurs.
        """
        self.assertFalse(self.office.siret in load_groupements_employeurs())

        rv = self.app.get(self.url_for('office.details', siret=self.office.siret))
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn(
            u"Cette entreprise est un groupement d'employeurs.",
            rv.data.decode(),
        )

    def test_download_regular_office(self):
        """
        Test the office PDF download
        """
        # normal behavior
        rv = self.app.get(self.url_for('office.download', siret=self.office.siret))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual('application/pdf', rv.mimetype)
        self.assertLess(1000, rv.content_length)

    def test_download_triggers_activity_log(self):
        with unittest.mock.patch('labonneboite.common.activity.log') as activity_log:
            self.app.get(self.url_for('office.download', siret=self.office.siret))
            activity_log.assert_called_with('telecharger-pdf', siret=self.office.siret)

    def test_download_missing_siret(self):
        """
        Test the office PDF download of a non existing office
        """
        # siret does not exist
        rv = self.app.get(self.url_for('office.download', siret='1234567890'))
        self.assertEqual(rv.status_code, 404)

    def test_download_of_office_having_buggy_naf(self):
        """
        Test the office PDF download of an office having NAF 9900Z.
        """
        self.db_session.query(Office).filter(Office.siret == self.office.siret).\
            update({"naf": "9900Z"}, synchronize_session="fetch")

        rv = self.app.get(self.url_for('office.download', siret=self.office.siret))
        self.assertEqual(rv.status_code, 200)

    def test_toggle_details_event(self):
        with unittest.mock.patch('labonneboite.common.activity.log') as activity_log:
            rv = self.app.post(self.url_for('office.toggle_details_event', siret=self.office.siret))
            activity_log.assert_called_with('afficher-details', siret=self.office.siret)
        self.assertEqual(rv.status_code, 200)
