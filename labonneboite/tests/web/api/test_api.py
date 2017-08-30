# coding: utf8

from urllib import urlencode
import datetime
import json

from labonneboite.common import scoring as scoring_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common.models import Office
from labonneboite.common.search import get_companies_for_naf_codes
from labonneboite.conf import settings
from labonneboite.tests.web.api.test_api_base import ApiBaseTest


class ApiGenericTest(ApiBaseTest):

    def test_happy_path(self):
        rome_code = u'D1408'
        naf_codes = [u'7320Z']
        latitude = 49.305658  # 15 Avenue François Mitterrand, 57290 Fameck, France.
        longitude = 6.116853
        distance = 100
        companies, _ = get_companies_for_naf_codes(
            naf_codes,
            latitude,
            longitude,
            distance,
            index=self.ES_TEST_INDEX,
            rome_code=rome_code,
        )
        sirets = [company.siret for company in companies]
        self.assertIn(u'00000000000001', sirets)
        self.assertIn(u'00000000000002', sirets)
        self.assertEqual(len(companies), 3)

    def test_headcount_filter(self):
        rome_code = u'D1408'
        naf_codes = [u'7320Z']
        latitude = 49.305658  # 15 Avenue François Mitterrand, 57290 Fameck, France.
        longitude = 6.116853
        distance = 100
        headcount_filter = settings.HEADCOUNT_SMALL_ONLY
        companies, _ = get_companies_for_naf_codes(
            naf_codes,
            latitude,
            longitude,
            distance,
            index=self.ES_TEST_INDEX,
            rome_code=rome_code,
            headcount_filter=headcount_filter,
        )
        sirets = [company.siret for company in companies]
        self.assertIn(u'00000000000001', sirets)  # this is the only office with small headcount
        self.assertNotIn(u'00000000000002', sirets)
        self.assertEqual(len(companies), 1)

    def test_naf_and_rome(self):
        """
        Ensure that those ROME codes can be used accurately in other tests.
        In order to ensure this, they should map to NAF codes used in the documents test data.
        """
        rome_to_naf_mapper = mapping_util.Rome2NafMapper()

        rome = u'D1405'
        naf_codes = rome_to_naf_mapper.map([rome])
        self.assertIn(u'7320Z', naf_codes)

        rome = u'M1801'
        naf_codes = rome_to_naf_mapper.map([rome])
        self.assertIn(u'9511Z', naf_codes)


class ApiSecurityTest(ApiBaseTest):
    """
    Test the API security params: `user`, `timestamp` and `signature`.
    """

    def test_wrong_timestamp_format(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        params['timestamp'] = u'2007'
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'timestamp format: %Y-%m-%dT%H:%M:%S')

    def test_expired_timestamp(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        params['timestamp'] = (datetime.datetime.now() - datetime.timedelta(minutes=20)).strftime('%Y-%m-%dT%H:%M:%S')
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'timestamp has expired')

    def test_invalid_signature(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        params['signature'] = u'x'
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'signature is invalid')

    def test_missing_user_param(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405,M1801',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'missing argument: user')

    def test_unknown_user(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405,M1801',
            'user': u'unknown',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'user is unknown')


class ApiCompanyListTest(ApiBaseTest):
    """
    Test the main API route: `company_list`.
    """

    def test_missing_communeid_or_latitudelongitude(self):
        params = self.add_security_params({
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'missing arguments: either commune_id or latitude and longitude')

    def test_unknown_commune_id(self):
        params = self.add_security_params({
            'commune_id': u'unknown',
            'distance': 20,
            'page': 1,
            'page_size': 2,
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'could not resolve latitude and longitude from given commune_id')

    def test_missing_rome_codes(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'missing argument: rome_codes')

    def test_all_rome_codes_in_rome_naf_mapping_have_a_description(self):
        rome_codes_from_rome_naf_mapping = mapping_util.load_rome_codes_from_rome_naf_mapping()
        rome_codes_from_rome_referential = settings.ROME_DESCRIPTIONS.keys()
        for rome_code in rome_codes_from_rome_naf_mapping:
            self.assertIn(rome_code, rome_codes_from_rome_referential)

    def test_all_naf_codes_in_rome_naf_mapping_have_a_description(self):
        naf_codes_from_rome_naf_mapping = mapping_util.load_naf_codes_from_rome_naf_mapping()
        naf_codes_from_naf_referential = settings.NAF_CODES
        for naf_code in naf_codes_from_rome_naf_mapping:
            self.assertIn(naf_code, naf_codes_from_naf_referential)

    def test_page_size_too_large(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'page': 2,
            'page_size': 101,
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'page_size is too large. Maximum value is 100')

    def test_wrong_distance_value(self):
        """
        A wrong value for `distance` should not trigger an error.
        """
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405',
            'distance': u'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)

    def test_rome_without_any_naf_should_not_trigger_any_error(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'K1701',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)

    def test_invalid_rome_codes(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'INVALID,INVALID_TOO',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv.data, u'invalid rome code: INVALID')

    def test_count_and_old_pagination(self):
        params = self.add_security_params({
            'distance': 10,
            'from_number': 1,
            'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
            'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
            'rome_codes': u'D1405',
            'to_number': 2,
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 3)
        self.assertEqual(len(data['companies']), 2)

    def test_count_pagination(self):
        params = self.add_security_params({
            'distance': 10,
            'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
            'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
            'page': 1,
            'page_size': 2,
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 3)
        self.assertEqual(len(data['companies']), 2)

    def test_query_by_commune_id(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'distance': 20,
            'page': 1,
            'page_size': 2,
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 1)
        self.assertEqual(len(data['companies']), 1)
        self.assertEqual(data['companies'][0]['siret'], u'00000000000004')

    def test_query_returns_urls_with_rome_code_context(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'distance': 20,
            'page': 1,
            'page_size': 2,
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 1)
        self.assertEqual(len(data['companies']), 1)
        self.assertIn(u'rome_code=D1405', data['companies'][0]['url'])

    def test_query_returns_scores_adjusted_to_rome_code_context(self):
        rome_code = u'D1405'
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'distance': 20,
            'page': 1,
            'page_size': 2,
            'rome_codes': rome_code,
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 1)
        self.assertEqual(len(data['companies']), 1)

        office_json = data['companies'][0]
        siret = office_json['siret']
        office = Office.query.get(siret)

        # ############### WARNING about matching scores vs hirings ################
        # Methods scoring_util.get_hirings_from_score
        # and scoring_util.get_score_from_hirings
        # rely on special coefficients SCORE_50_HIRINGS, SCORE_60_HIRINGS etc..
        # which values in github repository are *fake* and used for dev and test only.
        #
        # The real values are confidential, stored outside of github repo,
        # and only used in staging and production.
        #
        # This is designed so that you *CANNOT* guess the hirings based
        # on the score you see in production.
        # #########################################################################

        # general score/stars/hirings values (all rome_codes included)
        self.assertEqual(office.score, 71)
        self.assertEqual(office.stars, 3.55)
        self.assertEqual(scoring_util.get_hirings_from_score(office.score), 77.5)

        # now let's see values adjusted for current rome_code
        stars_for_rome_code = office_json['stars']
        self.assertEqual(stars_for_rome_code, office.get_stars_for_rome_code(rome_code))
        # stars from 0 to 5, score from 0 to 100 (x20)
        score_for_rome = stars_for_rome_code * 20.0
        self.assertEqual(score_for_rome, 3.0)
        self.assertEqual(scoring_util.get_hirings_from_score(score_for_rome), 0.6)

        # let's see how adjusting for this rome decreased hirings
        # from 77.5 (hirings for all rome_codes included)
        # to 0.6 (hirings for only the current rome_code)
        #
        # 0.6 is approx 1% of 77.5
        # which means that on average, companies of this naf_code hire 1% in this rome_code
        # and 99% in all other rome_codes associated to this naf_code
        #
        # let's check we can find back this 1% ratio in our rome-naf mapping data
        naf_code = office.naf
        rome_codes = mapping_util.MANUAL_NAF_ROME_MAPPING[naf_code].keys()
        total_naf_hirings = sum(mapping_util.MANUAL_NAF_ROME_MAPPING[naf_code][rome] for rome in rome_codes)
        self.assertEqual(total_naf_hirings, 7844)
        current_rome_hirings = mapping_util.MANUAL_NAF_ROME_MAPPING[naf_code][rome_code]
        self.assertEqual(current_rome_hirings, 52)
        # 52 hirings for this rome_code only is indeed roughly 1% of 7844 hirings for all rome_codes.
        # The match is not exact because some rounding occur during calculations, but you should
        # now get the main idea of how scores are adjusted to a given rome_code.

    def test_empty_result_does_not_crash(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'distance': 20,
            'page': 1,
            'page_size': 2,
            'rome_codes': u'J1103',  # no office has this ROME code
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 0)
        self.assertEqual(len(data['companies']), 0)

    def test_no_contact_details(self):
        """
        Test that sensitive contact data (such as `email`) is not be exposed in responses.
        """
        params = self.add_security_params({
            'distance': 20,
            'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
            'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(len(data['companies']), 3)
        for company in data['companies']:
            self.assertNotIn('email', company)

    def test_response_headers(self):
        params = self.add_security_params({
            'distance': 20,
            'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
            'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        self.assertEquals(rv.headers['Content-Type'], 'application/json')

    def test_romes_for_commune_id(self):
        """
        Perform queries in Caen to test the `rome_codes` param with one or more values.
        """
        # 1) Search for `D1405` ROME code only. We should get 1 result.
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 1)
        self.assertEqual(len(data['companies']), 1)
        self.assertEqual(data['companies'][0]['siret'], u'00000000000004')

        # 2) Search for `M1801` ROME code only. We should get 1 result.
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'M1801',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data['companies_count'], 1)
        self.assertEqual(len(data['companies']), 1)
        self.assertEqual(data['companies'][0]['siret'], u'00000000000005')

        # 3) Search for both `D1405` and `M1801` ROME codes. We should get a 400 response
        # since multi ROME search is not supported.
        # Reasons why we only support single-rome search are detailed in README.md
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': u'D1405,M1801',
            'user': u'labonneboite',
        })
        rv = self.app.get('/api/v1/company/?%s' % urlencode(params))
        self.assertEqual(rv.status_code, 400)
