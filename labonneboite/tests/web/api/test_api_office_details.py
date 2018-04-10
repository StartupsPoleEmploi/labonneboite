# coding: utf8

import json
from urllib import urlencode

import mock

from labonneboite.tests.web.api.test_api_base import ApiBaseTest


class ApiOfficeDetailsTest(ApiBaseTest):

    def test_query_office(self):
        """
        Test the `office_details` API route.
        """
        expected_result = {
            u'siret': u'00000000000001',
            u'naf': u'7320Z',
            u'name': u'OFFICE 1',
            u'naf_text': u'\xc9tudes de march\xe9 et sondages',
            u'url': u'%s/00000000000001/details' % self.HOME_URL,
            u'lon': 6.0,
            u'headcount_text': u'10 à 19 salariés',
            u'stars': 4.0,
            u'address': {
                u'city': u'BAYONVILLE-SUR-MAD',
                u'street_name': u'',
                u'street_number': u'',
                u'city_code': u'54055',
                u'zipcode': u'54890'
            },
            u'lat': 49.0,
        }
        params = self.add_security_params({'user': u'labonneboite'})
        rv = self.app.get('/api/v1/office/%s/details?%s' % (expected_result[u'siret'], urlencode(params)))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertDictEqual(data, expected_result)

    @mock.patch('labonneboite.conf.settings.API_INTERNAL_CONSUMERS', ['labonneboite'])
    def test_query_office_with_internal_user(self):
        """
        Test that internal services of Pôle emploi can have access to sensitive information.
        """
        params = self.add_security_params({'user': u'labonneboite'})
        rv = self.app.get('/api/v1/office/%s/details?%s' % ('00000000000001', urlencode(params)))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertIn(u'email', data)
        self.assertIn(u'phone', data)
        self.assertIn(u'website', data)

    def test_query_office_with_external_user(self):
        """
        Test that external services of Pôle emploi cannot have access to sensitive information.
        """
        params = self.add_security_params({'user': u'emploi_store_dev'})
        rv = self.app.get('/api/v1/office/%s/details?%s' % ('00000000000001', urlencode(params)))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertNotIn(u'email', data)
        self.assertNotIn(u'phone', data)
        self.assertNotIn(u'website', data)
