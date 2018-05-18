
import json
from urllib import urlencode
import time

from flask import url_for

from labonneboite.common.models import Office, OfficeAdminUpdate
from labonneboite.common import es
from labonneboite.scripts import create_index as script
from labonneboite.conf import settings
from labonneboite.common import mapping as mapping_util
from labonneboite.tests.web.api.test_api_base import ApiBaseTest
from labonneboite.tests.scripts.test_create_index import CreateIndexBaseTest


class ApiScriptsTest(ApiBaseTest,CreateIndexBaseTest):

    def setUp(self, *args, **kwargs):
        super(ApiScriptsTest, self).setUp(*args, **kwargs)


    def test_update_office_boost_flag_specific_romes_alternance(self):
        """
        Test `update_offices` boosted flag is present
        """
        office_to_update = OfficeAdminUpdate(
            sirets='00000000000007',
            name='Office 7',
            boost_alternance=True,
            romes_alternance_to_boost=u"D1507",  # Boost score only for this ROME.
        )
        office_to_update.save(commit=True)
        script.update_offices()

        # We need to wait before continuing.
        # If not, ES is not update and 00000000000007 is not consider as boosted...
        time.sleep(0.5)

        params = self.add_security_params({
            'commune_id': self.positions['metz']['commune_id'],
            'rome_codes': u'D1507',
            'user': u'labonneboite',
            'contract': u'alternance'
        })

        with self.test_request_context:
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data_list = json.loads(rv.data)

            self.assertEquals(len(data_list['companies']), 2)

            # 00000000000007 should be boosted and be the first result
            self.assertEquals(data_list['companies'][0]['siret'], '00000000000007')
            self.assertTrue(data_list['companies'][0]['boosted'])

            # 00000000000006 should not be boosted and be the second result
            self.assertFalse(data_list['companies'][1]['boosted'])


    def test_update_office_boost_flag_all_romes_alternance(self):
        """
        Test `update_offices` boosted flag is present when all romes are boosted
        """
        office_to_update = OfficeAdminUpdate(
            sirets='00000000000006',
            name='Office 6',
            boost_alternance=True
        )
        office_to_update.save()
        script.update_offices()

        params = self.add_security_params({
            'commune_id': self.positions['metz']['commune_id'],
            'rome_codes': u'D1507',
            'user': u'labonneboite',
            'contract': u'alternance'
        })

        with self.test_request_context:
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data_list = json.loads(rv.data)

            self.assertEquals(len(data_list['companies']), 2)

            # 00000000000006 is boosted and is the first result
            self.assertTrue(data_list['companies'][0]['boosted'])
            # 00000000000007 is not boosted and is the second result
            self.assertFalse(data_list['companies'][1]['boosted'])

