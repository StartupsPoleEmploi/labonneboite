
import json
from urllib import urlencode

from flask import url_for
import mock

from labonneboite.common.models import OfficeAdminUpdate
from labonneboite.common import es
from labonneboite.scripts import create_index as script
from labonneboite.tests.web.api.test_api_base import ApiBaseTest
from labonneboite.tests.scripts.test_create_index import CreateIndexBaseTest


class ApiScriptsTest(ApiBaseTest, CreateIndexBaseTest):

    @mock.patch.object(es.settings, 'ES_TIMEOUT', 20)
    def setUp(self, *args, **kwargs):
        super(ApiScriptsTest, self).setUp(*args, **kwargs)

    def test_update_office_boost_flag_specific_romes_alternance(self):
        """
        Test `update_offices` boosted flag is present
        """
        office_to_update = OfficeAdminUpdate(
            sirets='00000000000008',
            name='Office 8',
            boost_alternance=True,
            romes_alternance_to_boost=u"D1211",  # Boost score only for this ROME.
        )
        office_to_update.save(commit=True)
        script.update_offices()
        es.Elasticsearch().indices.flush()

        params = self.add_security_params({
            'commune_id': self.positions['nantes']['commune_id'],
            'rome_codes': u'D1211',
            'user': u'labonneboite',
            'contract': u'alternance'
        })

        with self.test_request_context:
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data_list = json.loads(rv.data)

            self.assertEquals(len(data_list['companies']), 2)

            # 00000000000008 should be boosted and be the first result
            self.assertEquals(data_list['companies'][0]['siret'], '00000000000008')
            self.assertTrue(data_list['companies'][0]['boosted'])

            # 00000000000009 should not be boosted and be the second result
            self.assertFalse(data_list['companies'][1]['boosted'])


    def test_update_office_boost_flag_all_romes_alternance(self):
        """
        Test `update_offices` boosted flag is present when all romes are boosted
        """
        office_to_update = OfficeAdminUpdate(
            sirets='00000000000009',
            name='Office 9',
            boost_alternance=True
        )
        office_to_update.save()
        script.update_offices()
        es.Elasticsearch().indices.flush()

        params = self.add_security_params({
            'commune_id': self.positions['nantes']['commune_id'],
            'rome_codes': u'D1211',
            'user': u'labonneboite',
            'contract': u'alternance'
        })

        with self.test_request_context:
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data_list = json.loads(rv.data)

            self.assertEquals(len(data_list['companies']), 2)

            # 00000000000009 is boosted and is the first result
            self.assertTrue(data_list['companies'][0]['boosted'])
            # 00000000000008 is not boosted and is the second result
            self.assertFalse(data_list['companies'][1]['boosted'])
