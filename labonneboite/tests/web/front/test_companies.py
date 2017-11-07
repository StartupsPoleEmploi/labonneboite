# coding: utf8
import unittest.mock

from labonneboite.common.models import Office
from labonneboite.common import pdf
from labonneboite.tests.test_base import DatabaseTest


class DownloadTest(DatabaseTest):

    def setUp(self):
        super().setUp()

        # Create an office.
        self.office = Office(
            departement='75',
            siret='78548035101646',
            company_name='NICOLAS',
            headcount='03',
            city_code='75110',
            zipcode='75010',
            naf='7320Z',
            tel='0100000000',
            score=80,
            x=2.3488,
            y=48.8534,
        )
        self.office.save()

        # Remove pdf file if it already exists
        pdf.delete_file(self.office)

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

        self.office.naf = '9900Z'
        self.office.save()

        rv = self.app.get(self.url_for('office.details', siret=self.office.siret))
        self.assertEqual(rv.status_code, 200)

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
        self.office.naf = '9900Z'
        self.office.save()

        rv = self.app.get(self.url_for('office.download', siret=self.office.siret))
        self.assertEqual(rv.status_code, 200)

    def test_toggle_details_event(self):
        with unittest.mock.patch('labonneboite.common.activity.log') as activity_log:
            rv = self.app.post(self.url_for('office.toggle_details_event', siret=self.office.siret))
            activity_log.assert_called_with('afficher-details', siret=self.office.siret)
        self.assertEqual(rv.status_code, 200)
