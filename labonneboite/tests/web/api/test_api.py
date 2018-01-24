# coding: utf8

import datetime
import json
from urllib import urlencode
import urlparse
import mock

from flask import url_for
from labonneboite.common import scoring as scoring_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common.models import Office
from labonneboite.common.search import fetch_companies
from labonneboite.conf import settings
from labonneboite.tests.web.api.test_api_base import ApiBaseTest


class ApiGenericTest(ApiBaseTest):

    def test_happy_path(self):
        rome_code = u'D1408'
        naf_codes = [u'7320Z']
        latitude = 49.305658  # 15 Avenue François Mitterrand, 57290 Fameck, France.
        longitude = 6.116853
        distance = 100
        companies, _, _ = fetch_companies(
            naf_codes,
            rome_code,
            latitude,
            longitude,
            distance,
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
        headcount = settings.HEADCOUNT_SMALL_ONLY
        companies, _, _ = fetch_companies(
            naf_codes,
            rome_code,
            latitude,
            longitude,
            distance,
            headcount=headcount,
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
        rome = u'D1405'
        naf_codes = mapping_util.map_romes_to_nafs([rome])
        self.assertIn(u'7320Z', naf_codes)

        rome = u'M1801'
        naf_codes = mapping_util.map_romes_to_nafs([rome])
        self.assertIn(u'9511Z', naf_codes)


class ApiSecurityTest(ApiBaseTest):
    """
    Test the API security params: `user`, `timestamp` and `signature`.
    """

    def test_wrong_timestamp_format(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            params['timestamp'] = u'2007'
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'timestamp format: %Y-%m-%dT%H:%M:%S')

    def test_expired_timestamp(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            params['timestamp'] = (
                datetime.datetime.now() - datetime.timedelta(minutes=20)
            ).strftime('%Y-%m-%dT%H:%M:%S')
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'timestamp has expired')

    def test_invalid_signature(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            params['signature'] = u'x'
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'signature is invalid')

    def test_missing_user_param(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405,M1801',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'missing argument: user')

    def test_unknown_user(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405,M1801',
                'user': u'unknown',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'user is unknown')


class ApiCompanyListTest(ApiBaseTest):
    """
    Test the main API route: `company_list`.
    """

    def test_missing_communeid_or_latitudelongitude(self):
        with self.test_request_context:
            params = self.add_security_params({
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data,
                u'Invalid request argument: missing arguments: either commune_id or latitude and longitude')

    def test_unknown_commune_id(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': u'unknown',
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data,
                u'Invalid request argument: could not resolve latitude and longitude from given commune_id')

    def test_correct_headcount_text(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['pau']['commune_id'],
                'distance': 10,
                'rome_codes': u'B1603',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['headcount_text'], u'10 000 salariés et plus')

    def test_missing_rome_codes(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'Invalid request argument: missing rome_codes')

    def test_page_size_too_large(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'page': 2,
                'page_size': 101,
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'Invalid request argument: page_size is too large. Maximum value is 100')

    def test_wrong_distance_value(self):
        """
        A wrong value for `distance` should not trigger an error.
        """
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405',
                'distance': u'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)

    def test_rome_without_any_naf_should_not_trigger_any_error(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'K1701',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)

    def test_invalid_rome_codes(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'INVALID,INVALID_TOO',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertTrue(rv.data.startswith(u'Invalid request argument: Unknown rome_code: INVALID'))

    def test_count_pagination(self):
        with self.test_request_context:
            params = self.add_security_params({
                'distance': 10,
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'page': 1,
                'page_size': 2,
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 3)
            self.assertEqual(len(data['companies']), 2)

    def test_query_by_commune_id(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000004')

    def test_query_returns_urls_with_rome_code_context(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertIn(u'rome_code=D1405', data['companies'][0]['url'])

    def test_query_returns_scores_adjusted_to_rome_code_context(self):
        with self.test_request_context:
            rome_code = u'D1405'
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': rome_code,
                'user': u'labonneboite',
            })

            # The example in this test has a very low score (below SCORE_FOR_ROME_MINIMUM),
            # which is why we need to lower the threshold just for this test, in order
            # to be able to compute back the score from the stars.
            with mock.patch.object(scoring_util, 'SCORE_FOR_ROME_MINIMUM', 0):
                rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
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

                # general score/hirings values (all rome_codes included)
                self.assertEqual(office.score, 71)
                self.assertEqual(scoring_util.get_hirings_from_score(office.score), 77.5)

                # now let's see values adjusted for current rome_code
                stars_for_rome_code = office_json['stars']
                self.assertEqual(stars_for_rome_code, office.get_stars_for_rome_code(rome_code))
                score_for_rome = scoring_util.get_score_from_stars(stars_for_rome_code)
                self.assertEqual(round(score_for_rome, 5), 4.0)
                self.assertEqual(round(scoring_util.get_hirings_from_score(score_for_rome), 5), 0.8)

                # let's see how adjusting for this rome decreased hirings
                # from 77.5 (hirings for all rome_codes included)
                # to 0.8 (hirings for only the current rome_code)
                #
                # 0.8 is approx 1% of 77.5
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
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': u'J1103',  # no office has this ROME code
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 0)
            self.assertEqual(len(data['companies']), 0)

    def test_no_contact_details(self):
        """
        Test that sensitive contact data (such as `email`) is not exposed in responses.
        """
        with self.test_request_context:
            params = self.add_security_params({
                'distance': 20,
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(len(data['companies']), 3)
            for company in data['companies']:
                self.assertNotIn('email', company)

    def test_response_headers(self):
        with self.test_request_context:
            params = self.add_security_params({
                'distance': 20,
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            self.assertEquals(rv.headers['Content-Type'], 'application/json')

    def test_romes_for_commune_id(self):
        """
        Perform queries in Caen to test the `rome_codes` param with one or more values.
        """
        with self.test_request_context:
            # 1) Search for `D1405` ROME code only. We should get 1 result.
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
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
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
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
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)

    def test_wrong_naf_value(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': u'D1508',
                'naf_codes': u'INVALID,INVALID_TOO',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'Invalid request argument: NAF code(s): INVALID INVALID_TOO')

    def test_same_rome_with_no_naf_filters(self):
        with self.test_request_context:
            # 1) No NAF Code => 2 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': u'D1508',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            self.assertNotEqual(data['companies'][0]['naf'], data['companies'][1]['naf'])

    def test_same_rome_with_one_naf_filters(self):
        with self.test_request_context:
            # 1) NAF Code : 4711C => 1 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': u'D1508',
                'naf_codes': u'4711C',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000006')

            # 2) NAF Code : 5610C => 1 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': u'D1508',
                'naf_codes': u'5610C',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000007')

    def test_same_rome_with_two_naf_filters(self):
        with self.test_request_context:
            # 1) NAF codes : 5610C,4711C => 2 results expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': u'D1508',
                'naf_codes': u'5610C,4711C',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)

    def test_same_rome_with_unrelated_naf_filters(self):
        with self.test_request_context:
            # NAF Code : 9499Z => 0 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': u'D1508',
                'naf_codes': u'9499Z',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertIn(u'Invalid request argument: NAF code(s): 9499Z. Possible values : ', rv.data)

    def test_wrong_value_in_sort(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['nantes']['commune_id'],
                'rome_codes': u'D1211',
                'sort': u'INVALID',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'Invalid request argument: sort. Possible values : score, distance')

    def test_sort_by_distance(self):
        with self.test_request_context:
            # Nantes in first place, then Reze
            params = self.add_security_params({
                'commune_id': self.positions['nantes']['commune_id'],
                'rome_codes': u'D1211',
                'sort': u'distance',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            self.assertEqual(data["companies"][0]['siret'], u'00000000000008')
            self.assertEqual(data["companies"][1]['siret'], u'00000000000009')
            self.assertLess(data["companies"][0]['distance'], data["companies"][1]['distance'])

    def test_sort_by_score(self):
        with self.test_request_context:
            # Reze in first place, then Nantes
            params = self.add_security_params({
                'commune_id': self.positions['nantes']['commune_id'],
                'rome_codes': u'D1211',
                'sort': u'score',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set([u'00000000000009', u'00000000000008']))

    def test_wrong_contract_value(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['lille']['commune_id'],
                'rome_codes': u'D1213',
                'user': u'labonneboite',
                'contract': u'Invalid'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'Invalid request argument: contract. Possible values : all, alternance')

    def test_contract_all(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['lille']['commune_id'],
                'rome_codes': u'D1213',
                'user': u'labonneboite',
                'contract': u'all'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)

    def test_contract_alternance_only(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['lille']['commune_id'],
                'rome_codes': u'D1213',
                'user': u'labonneboite',
                'contract': u'alternance'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000011')
            self.assertEqual(data['companies'][0]['alternance'], True)

    def test_wrong_headcount_value(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': u'M1202',
                'user': u'labonneboite',
                'headcount': u'INVALID'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, u'Invalid request argument: headcount. Possible values : small, big, all')

    def test_headcount_all(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': u'M1202',
                'user': u'labonneboite',
                'headcount': u'all'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)

    def test_headcount_small(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': u'M1202',
                'user': u'labonneboite',
                'headcount': u'small'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000012')
            self.assertEqual(data['companies'][0]['headcount_text'], u'10 à 19 salariés')

    def test_headcount_big(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': u'M1202',
                'user': u'labonneboite',
                'headcount': u'big'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000013')
            self.assertEqual(data['companies'][0]['headcount_text'], u'100 à 199 salariés')

    def test_contact_mode(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': u'D1405',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000004')
            self.assertEqual(data['companies'][0]['contact_mode'], u'Envoyer un CV et une lettre de motivation')


    def test_flag_alternance(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['poitiers']['commune_id'],
                'rome_codes': u'B1603',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            sirets = {c['siret']: c for c in data['companies']}
            self.assertEqual(sorted(sirets.keys()), [u'00000000000015', u'00000000000016'])
            self.assertEqual(sirets[u'00000000000015']['alternance'], False)
            self.assertEqual(sirets[u'00000000000016']['alternance'], True)


    def test_department_filters(self):
        with self.test_request_context:
            # Invalid departments filter => Expected error message
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': u'N1202',
                'user': u'labonneboite',
                'departments': u'75,XX,YY'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 400)
            self.assertIn(u'Invalid request argument: departments : XX, YY', rv.data)

            # no departments filter => Expected 2 results
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': u'N1202',
                'user': u'labonneboite'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set([u'00000000000017', u'00000000000018']))

            # Check two departments => Expected 2 results
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': u'N1202',
                'user': u'labonneboite',
                'departments': u'75,92'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set([u'00000000000017', u'00000000000018']))

            # Check department 75 => Expected 1 result
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': u'N1202',
                'user': u'labonneboite',
                'departments': u'75'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000017')

            # Check department 92 => Expected 1 result
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': u'N1202',
                'user': u'labonneboite',
                'departments': u'92'
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(data['companies'][0]['siret'], u'00000000000018')

    def test_filters_in_api_response(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)

            # Check distance filter
            self.assertEqual(data['filters']['distance']['less_30_km'], 4)
            self.assertEqual(data['filters']['distance']['less_50_km'], 5)
            self.assertEqual(data['filters']['distance']['less_100_km'], 6)
            self.assertEqual(data['filters']['distance']['france'], 7)

            # Check naf filter
            nafs_expected = {
                u'4910Z': [u'4910Z', 2, u'Transport ferroviaire interurbain de voyageurs'],
                u'4920Z': [u'4920Z', 1, u'Transports ferroviaires de fret'],
            }
            self.assertEqual(len(nafs_expected), len(data['filters']['naf']))
            for naf_filter in data['filters']['naf']:
                naf_expected = nafs_expected[naf_filter['code']]

                self.assertEqual(naf_expected[0], naf_filter['code'])
                self.assertEqual(naf_expected[1], naf_filter['count'])
                self.assertEqual(naf_expected[2], naf_filter['label'])

            # Check headcount filter
            self.assertEqual(data['filters']['headcount']['small'], 2)
            self.assertEqual(data['filters']['headcount']['big'], 1)

            # Check contract filter
            self.assertEqual(data['filters']['contract']['all'], 3)
            self.assertEqual(data['filters']['contract']['alternance'], 1)


    def test_filters_when_filtering_by_naf(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'naf_codes': u'4910Z',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            nafs_expected = {
                u'4910Z': [u'4910Z', 2, u'Transport ferroviaire interurbain de voyageurs'],
                u'4920Z': [u'4920Z', 1, u'Transports ferroviaires de fret'],
            }
            self.assertEqual(len(nafs_expected), len(data['filters']['naf']))
            for naf_filter in data['filters']['naf']:
                naf_expected = nafs_expected[naf_filter['code']]
                # FIXME naf_expected never used?


    def test_filters_when_filtering_by_headcount(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'headcount': u'big',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['filters']['headcount']['small'], 2)
            self.assertEqual(data['filters']['headcount']['big'], 1)

            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'headcount': u'small',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['filters']['headcount']['small'], 2)
            self.assertEqual(data['filters']['headcount']['big'], 1)

    def test_filters_when_filtering_by_contract(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'contract': u'all',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['filters']['contract']['all'], 3)
            self.assertEqual(data['filters']['contract']['alternance'], 1)

            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'contract': u'alternance',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['filters']['contract']['all'], 3)
            self.assertEqual(data['filters']['contract']['alternance'], 1)

    def test_filters_when_filtering_by_distance(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'distance': u'50',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)

            self.assertEqual(data['filters']['distance']['less_10_km'], 3)
            self.assertEqual(data['filters']['distance']['less_30_km'], 4)
            self.assertEqual(data['filters']['distance']['less_50_km'], 5)
            self.assertEqual(data['filters']['distance']['less_100_km'], 6)
            self.assertEqual(data['filters']['distance']['france'], 7)

            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': u'N4403',
                'distance': u'100',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_filter_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['filters']['distance']['less_10_km'], 3)
            self.assertEqual(data['filters']['distance']['less_30_km'], 4)
            self.assertEqual(data['filters']['distance']['less_50_km'], 5)
            self.assertEqual(data['filters']['distance']['less_100_km'], 6)
            self.assertEqual(data['filters']['distance']['france'], 7)

class ApiCompanyListTrackingCodesTest(ApiBaseTest):

    def assertTrackingCodesEqual(self, company_url, utm_medium, utm_source, utm_campaign):
        url_query = urlparse.urlparse(company_url)[4]
        url_params = urlparse.parse_qs(url_query)

        self.assertIn('utm_medium', url_params)
        self.assertEqual([utm_medium], url_params.get('utm_medium'))
        self.assertIn('utm_source', url_params)
        self.assertEqual([utm_source], url_params.get('utm_source'))
        self.assertIn('utm_campaign', url_params)
        self.assertEqual([utm_campaign], url_params.get('utm_campaign'))

    def test_api_urls_include_google_analytics_tracking(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['pau']['commune_id'],
                'distance': 10,
                'rome_codes': u'B1603',
                'user': u'labonneboite',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            company_url = data['companies'][0]['url']

        self.assertTrackingCodesEqual(company_url, 'web', 'api__labonneboite', 'api__labonneboite')

    def test_api_urls_include_google_analytics_tracking_with_origin_user(self):
        with self.test_request_context:
            params = self.add_security_params({
                'commune_id': self.positions['pau']['commune_id'],
                'distance': 10,
                'rome_codes': u'B1603',
                'user': u'labonneboite',
                'origin_user': 'someuser',
            })
            rv = self.app.get('%s?%s' % (url_for("api.company_list"), urlencode(params)))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)

            company_url = data['companies'][0]['url']
            self.assertTrackingCodesEqual(company_url, 'web', 'api__labonneboite', 'api__labonneboite__someuser')
