import json
from unittest import mock

from flask import url_for

from labonneboite.common.models import OfficeAdminUpdate
from labonneboite.common import es
from labonneboite.scripts import create_index as script
from labonneboite.tests.web.api.test_api_base import ApiBaseTest
from labonneboite.tests.scripts.test_create_index import CreateIndexBaseTest


class ApiScriptsTest(ApiBaseTest, CreateIndexBaseTest):

    @mock.patch.object(es.settings, 'ES_TIMEOUT', 90)
    def setUp(self, *args, **kwargs):
        super(ApiScriptsTest, self).setUp(*args, **kwargs)

    def test_update_office_boost_flag_specific_romes(self):
        """
        Test `update_offices` boosted flag is present
        """
        office_to_update = OfficeAdminUpdate(
            sirets='00000000000008',
            name='Office 8',
            boost=True,
            romes_to_boost="D1211",  # Boost score only for this ROME.
        )
        office_to_update.save(commit=True)
        script.update_offices(OfficeAdminUpdate)
        es.Elasticsearch().indices.flush()

        params = self.add_security_params({
            'commune_id': self.positions['nantes']['commune_id'],
            'rome_codes': 'D1211',
            'user': 'labonneboite'
        })

        with self.test_request_context():
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data_list = json.loads(rv.data.decode())

            self.assertEqual(len(data_list['companies']), 2)

            # 00000000000008 should be boosted and be the first result
            self.assertEqual(data_list['companies'][0]['siret'], '00000000000008')
            self.assertTrue(data_list['companies'][0]['boosted'])

            # 00000000000009 should not be boosted and be the second result
            self.assertFalse(data_list['companies'][1]['boosted'])

    def test_update_office_boost_flag_all_romes(self):
        """
        Test `update_offices` boosted flag is present when all romes are boosted
        """
        office_to_update = OfficeAdminUpdate(
            sirets='00000000000009',
            name='Office 9',
            boost=True
        )
        office_to_update.save()
        script.update_offices(OfficeAdminUpdate)
        es.Elasticsearch().indices.flush()

        params = self.add_security_params({
            'commune_id': self.positions['nantes']['commune_id'],
            'rome_codes': 'D1211',
            'user': 'labonneboite'
        })

        with self.test_request_context():
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200, msg=rv.data)
            data_list = json.loads(rv.data.decode())

            self.assertEqual(len(data_list['companies']), 2)

            # 00000000000009 is boosted and is the first result
            self.assertDictContainsSubset(dict(
                siret='00000000000009',
                boosted=True,
            ), data_list['companies'][0])
            # 00000000000008 is not boosted and is the second result
            self.assertDictContainsSubset(dict(
                siret='00000000000008',
                boosted=False,
            ), data_list['companies'][1])
