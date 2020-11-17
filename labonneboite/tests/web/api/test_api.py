
import datetime
import json
from unittest import mock
import urllib.parse

from flask import url_for
from labonneboite.common import autocomplete
from labonneboite.common import hiring_type_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common import pagination
from labonneboite.common import scoring as scoring_util
from labonneboite.common.models import Office
from labonneboite.common.search import fetch_offices
from labonneboite.conf import settings
from labonneboite.tests.web.api.test_api_base import ApiBaseTest


class ApiGenericTest(ApiBaseTest):

    def test_happy_path(self):
        rome_code = 'D1405'
        naf_codes = ['4646Z']
        latitude = 49.305658  # 15 Avenue François Mitterrand, 57290 Fameck, France.
        longitude = 6.116853
        distance = 100
        companies, _, _ = fetch_offices(
            naf_codes,
            [rome_code],
            latitude,
            longitude,
            distance,
            hiring_type=hiring_type_util.DPAE,
        )
        sirets = [company.siret for company in companies]
        self.assertIn('00000000000001', sirets)
        self.assertIn('00000000000002', sirets)
        self.assertEqual(len(companies), 3)

    def test_headcount_filter(self):
        rome_code = 'D1405'
        naf_codes = ['4646Z']
        latitude = 49.305658  # 15 Avenue François Mitterrand, 57290 Fameck, France.
        longitude = 6.116853
        distance = 100
        headcount = settings.HEADCOUNT_SMALL_ONLY
        companies, _, _ = fetch_offices(
            naf_codes,
            [rome_code],
            latitude,
            longitude,
            distance,
            headcount=headcount,
            hiring_type=hiring_type_util.DPAE,
        )
        sirets = [company.siret for company in companies]
        self.assertIn('00000000000001', sirets)  # this is the only office with small headcount
        self.assertNotIn('00000000000002', sirets)
        self.assertEqual(len(companies), 1)

    def test_office_distance_has_one_digit(self):
        rome_code = 'D1405'
        naf_codes = ['4646Z']
        latitude = 49.305658  # 15 Avenue François Mitterrand, 57290 Fameck, France.
        latitude += 0.1  # original coordinates will unfortunately give a distance with 0 digit
        longitude = 6.116853
        distance = 100
        companies, _, _ = fetch_offices(
            naf_codes,
            [rome_code],
            latitude,
            longitude,
            distance,
            hiring_type=hiring_type_util.DPAE,
        )
        self.assertEqual(len(companies), 3)
        # what is important here is that there is one digit
        self.assertEqual(companies[0].distance, 45.9)

    def test_rome_and_naf_codes_used_in_tests_are_in_actual_mapping(self):
        """
        Ensure that those ROME and NAF codes can be used accurately in tests.
        """
        self.assertIn('4646Z', mapping_util.map_romes_to_nafs(['D1405']))
        self.assertIn('9511Z', mapping_util.map_romes_to_nafs(['M1801']))
        self.assertIn('4771Z', mapping_util.map_romes_to_nafs(['D1508']))
        self.assertIn('4711F', mapping_util.map_romes_to_nafs(['D1508']))
        self.assertIn('9529Z', mapping_util.map_romes_to_nafs(['D1211']))
        self.assertIn('4741Z', mapping_util.map_romes_to_nafs(['D1211']))
        self.assertIn('4752B', mapping_util.map_romes_to_nafs(['D1213']))
        self.assertIn('7022Z', mapping_util.map_romes_to_nafs(['M1202']))
        self.assertIn('3212Z', mapping_util.map_romes_to_nafs(['B1603']))
        self.assertIn('5229A', mapping_util.map_romes_to_nafs(['N1202']))
        self.assertIn('4910Z', mapping_util.map_romes_to_nafs(['N4403']))
        self.assertIn('4920Z', mapping_util.map_romes_to_nafs(['N4403']))
        self.assertIn('7022Z', mapping_util.map_romes_to_nafs(['M1202']))


class ApiSecurityTest(ApiBaseTest):
    """
    Test the API security params: `user`, `timestamp` and `signature`.
    """

    def test_wrong_timestamp_format(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            params['timestamp'] = '2007'
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'timestamp format: %Y-%m-%dT%H:%M:%S')

    def test_expired_timestamp(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            params['timestamp'] = (
                datetime.datetime.now() - datetime.timedelta(minutes=20)
            ).strftime('%Y-%m-%dT%H:%M:%S')
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'timestamp has expired')

    def test_invalid_signature(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            params['signature'] = 'x'
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'signature is invalid')

    def test_missing_user_param(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405,M1801',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'missing argument: user')

    def test_unknown_user(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405,M1801',
                'user': 'unknown',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'user is unknown')


class ApiCompanyListTest(ApiBaseTest):
    """
    Test the main API route: `company_list`.
    """

    def test_happy_path(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_unknown_contract(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
                'contract': 'unicorn',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)

    def test_contract_all(self):
        """
        Deprecated parameter value is no longer supported. Only 'dpae' and 'alternance' are.
        """
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['lille']['commune_id'],
                'rome_codes': 'D1213',
                'user': 'labonneboite',
                'contract': 'all'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)

    def test_contract_dpae(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['lille']['commune_id'],
                'rome_codes': 'D1213',
                'user': 'labonneboite',
                'contract': 'dpae'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)

    def test_contract_alternance(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['lille']['commune_id'],
                'rome_codes': 'D1213',
                'user': 'labonneboite',
                'contract': 'alternance',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000011')
            self.assertTrue(data['companies'][0]['alternance'])
            self.assertIn('https://labonnealternance.pole-emploi.fr/details-entreprises/', data['companies'][0]['url'])

    def test_missing_communeid_or_latitudelongitude(self):
        with self.test_request_context():
            params = self.add_security_params({
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(
                rv.data,
                b'Invalid request argument: missing arguments: either commune_id or departments or both latitude and longitude'
            )

    def test_invalid_longitude_or_latitude(self):
        with self.test_request_context():
            params = self.add_security_params({
                'rome_codes': 'D1405',
                'user': 'labonneboite',
                'latitude': '42',
                'longitude': 'unparsable',
            })
            rv = self.app.get(self.url_for('api.company_list', **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(
                rv.data,
                b'Invalid request argument: latitude and longitude must be float'
            )

    def test_unknown_commune_id(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': 'unknown',
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(
                rv.data,
                b'Invalid request argument: could not resolve latitude and longitude from given commune_id'
            )

    def test_correct_headcount_text(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['pau']['commune_id'],
                'distance': 10,
                'rome_codes': 'B1603',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['headcount_text'], '10 000 salariés et plus')

    def test_page_size_too_large(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'page': 2,
                'page_size': pagination.OFFICES_MAXIMUM_PAGE_SIZE + 1,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(
                rv.data.decode(),
                'Invalid request argument: page_size is too large. Maximum value is %s' % (
                    pagination.OFFICES_MAXIMUM_PAGE_SIZE
                )
            )

    def test_maximum_page_size_is_ok(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'page': 1,
                'page_size': pagination.OFFICES_MAXIMUM_PAGE_SIZE,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_exotic_page_size_is_ok(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'page': 1,
                'page_size': 42,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_zero_distance_value(self):
        """
        A 0 value for `distance` should not trigger an error since MAP/MHP is actively
        using this type of request in production.
        """
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'distance': '0',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_string_distance_value(self):
        """
        A wrong value for `distance` should trigger an error.
        """
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'distance': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)

    def test_missing_rome_codes(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(
                rv.data,
                b'Invalid request argument: you must use rome_codes or rome_codes_keyword_search'
            )

    def test_rome_codes_search_by_keyword_normal_case(self):
        self.es.index(index=settings.ES_INDEX, doc_type='ogr', id=1, body={
            'ogr_code': '10974',
            'ogr_description': 'Animateur commercial / Animatrice commerciale',
            'rome_code': 'D1501',
            'rome_description': 'Animation de vente'
        })
        self.es.indices.flush(index=settings.ES_INDEX)

        with self.test_request_context():
            rome_codes = 'D1501'
            rome_codes_keyword_search = 'animateur vente'

            # ensure the keyword search matches the right rome_code
            suggestions = autocomplete.build_job_label_suggestions(rome_codes_keyword_search)
            self.assertEqual(suggestions[0]['id'], rome_codes)

            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'user': 'labonneboite',
                'rome_codes': rome_codes,
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data_direct_search = json.loads(rv.data.decode())

            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'user': 'labonneboite',
                'rome_codes_keyword_search': rome_codes_keyword_search,
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data_keyword_search = json.loads(rv.data.decode())

            self.assertEqual(data_direct_search, data_keyword_search)

    def test_rome_codes_search_by_keyword_when_accented_unicode_character(self):
        self.es.index(index=settings.ES_INDEX, doc_type='ogr', id=1, body={
            'ogr_code': 'OGRCODE',
            'ogr_description': 'Secrétaire de l\'enfer',
            'rome_code': 'M1607',
            'rome_description': 'Secrétariat'
        })
        self.es.indices.flush(index=settings.ES_INDEX)

        with self.test_request_context():
            rome_codes_keyword_search = 'secrétaire'
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'user': 'labonneboite',
                # unicode parameter rome_codes_keyword_search needs to be properly encoded
                'rome_codes_keyword_search': rome_codes_keyword_search.encode('utf8'),
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['rome_code'], 'M1607')
            self.assertEqual(data['rome_label'], 'Secrétariat')

    def test_rome_codes_search_by_keyword_when_no_match_found(self):
        with self.test_request_context():
            rome_codes_keyword_search = 'unicorn'

            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'user': 'labonneboite',
                'rome_codes_keyword_search': rome_codes_keyword_search,
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(
                rv.data,
                b'Invalid request argument: No match found for rome_codes_keyword_search.'
            )

    def test_rome_code_and_label_are_present_in_response(self):
        with self.test_request_context():
            rome = 'D1501'
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'user': 'labonneboite',
                'rome_codes': rome,
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            data = json.loads(rv.data.decode())
            self.assertEqual(data['rome_code'], rome)
            self.assertEqual(data['rome_label'], 'Animation de vente')

    def test_ok_if_distance_value_is_zero(self):
        """
        A wrong value for `distance` should trigger an error.
        """
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'distance': '0',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_error_when_latitude_or_longitude_are_empty(self):
        """
        If latitude or longitude are empty, throw a Bad Request Error
        """
        with self.test_request_context():
            params = self.add_security_params({
                'latitude': '',
                'longitude': '',
                'rome_codes': 'D1405',
                'distance': '10',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)

    def test_ok_when_latitude_or_longitude_equal_zero(self):
        """
        If latitude and longitude equal, throw No Error
        """
        with self.test_request_context():
            params = self.add_security_params({
                'latitude': '0',
                'longitude': '0',
                'rome_codes': 'D1405',
                'distance': '10',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_error_when_latitude_or_longitude_are_strings(self):
        """
        If latitude or longitude are empty, throw a Bad Request Error
        """
        with self.test_request_context():
            params = self.add_security_params({
                'latitude': 'xxx',
                'longitude': 'xxx',
                'rome_codes': 'D1405',
                'distance': '10',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)

    def test_rome_without_any_naf_should_not_trigger_any_error(self):
        with self.test_request_context():
            rome_with_naf_mapping = 'K1706'
            rome_without_naf_mapping = 'L1510'
            self.assertIn(rome_with_naf_mapping, mapping_util.MANUAL_ROME_NAF_MAPPING)
            self.assertNotIn(rome_without_naf_mapping, mapping_util.MANUAL_ROME_NAF_MAPPING)
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': rome_without_naf_mapping,
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_invalid_rome_codes(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'INVALID,INVALID_TOO',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertTrue(rv.data.decode().startswith('Invalid request argument: Unknown rome_code: INVALID'))

    def test_count_pagination(self):
        with self.test_request_context():
            params = self.add_security_params({
                'distance': 10,
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 3)
            self.assertEqual(len(data['companies']), 2)

    def test_query_by_commune_id(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)

    def test_query_by_departement(self):
        """
        test 1 dpt without geoloc
        """
        with self.test_request_context():
            params = self.add_security_params({
                'departments': '14',
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000004')
            self.assertFalse('distance' in data['companies'][0])

    def test_query_by_multiple_departements(self):
        """
        test several dpt without geoloc
        """
        with self.test_request_context():
            params = self.add_security_params({
                'departments': '14,57',
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405,D1211',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(
                set([c['siret'] for c in data['companies']]),
                set(['00000000000004', '00000000000007'])
            )
            self.assertFalse('distance' in data['companies'][0])

    def test_query_by_departement_geoloc(self):
        """
        test dpt+geoloc (case labonneformation)
        """
        with self.test_request_context():
            params = self.add_security_params({
                'distance': 50,
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'departments': '57',
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405,D1211',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000007')

    def test_query_by_departement_invalid_query_sort(self):
        """
        test dpt without geoloc with distance sort
        """
        with self.test_request_context():
            params = self.add_security_params({
                'departments': '14',
                'sort': 'distance',
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertTrue(rv.data.decode().startswith('Invalid request argument'))

    def test_query_by_departement_invalid_query_filter(self):
        """
        test dpt without geoloc with distance filter
        """
        with self.test_request_context():
            params = self.add_security_params({
                'departments': '14',
                'distance': 50,
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertTrue(rv.data.decode().startswith('Invalid request argument'))

    def test_query_returns_urls_with_rome_code_context(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertIn('rome_code=D1405', data['companies'][0]['url'])

    def test_query_returns_scores_adjusted_to_rome_code_context(self):
        with self.test_request_context():
            rome_code = 'D1405'
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': rome_code,
                'user': 'labonneboite',
            })

            # The example in this test has a very low score (below SCORE_FOR_ROME_MINIMUM),
            # which is why we need to lower the threshold just for this test, in order
            # to be able to compute back the score from the stars.
            with mock.patch.object(scoring_util, 'SCORE_FOR_ROME_MINIMUM', 0):
                rv = self.app.get(self.url_for("api.company_list", **params))
                self.assertEqual(rv.status_code, 200)
                data = json.loads(rv.data.decode())
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
                self.assertEqual(stars_for_rome_code, 3.8)
                self.assertEqual(stars_for_rome_code, office.get_stars_for_rome_code(rome_code))

                score_for_rome = office.get_score_for_rome_code(rome_code)
                self.assertEqual(score_for_rome, 50.0)
                self.assertEqual(round(scoring_util.get_hirings_from_score(score_for_rome), 1), 10.0)

                # let's see how adjusting for this rome decreased hirings
                # from 77.5 (hirings for all rome_codes included)
                # to 10.0 (hirings for only the current rome_code)
                #
                # 10.0 is approx 13% of 77.5
                # which means that on average, companies of this naf_code hire 13% in this rome_code
                # and 87% in all other rome_codes associated to this naf_code
                #
                # let's check we can find back this 13% ratio in our rome-naf mapping data
                naf_code = office.naf
                rome_codes = list(mapping_util.MANUAL_NAF_ROME_MAPPING[naf_code].keys())
                total_naf_hirings = sum(mapping_util.MANUAL_NAF_ROME_MAPPING[naf_code][rome] for rome in rome_codes)
                self.assertEqual(total_naf_hirings, 2681)
                current_rome_hirings = mapping_util.MANUAL_NAF_ROME_MAPPING[naf_code][rome_code]
                self.assertEqual(current_rome_hirings, 329)
                # 329 hirings for this rome_code only is indeed roughly 12-13% of 2681 hirings for all rome_codes.
                # The match is not exact because some rounding occur during calculations, but you should
                # now get the main idea of how scores are adjusted to a given rome_code.

    def test_empty_result_does_not_crash(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': 'J1103',  # no office has this ROME code
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 0)
            self.assertEqual(len(data['companies']), 0)

    def test_sensitive_contact_data_such_as_email_is_not_exposed(self):
        with self.test_request_context():
            params = self.add_security_params({
                'distance': 20,
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(len(data['companies']), 3)
            for company in data['companies']:
                self.assertNotIn('email', company)

    def test_response_headers(self):
        with self.test_request_context():
            params = self.add_security_params({
                'distance': 20,
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv.headers['Content-Type'], 'application/json')

    def test_multi_romes_search_is_supported_for_both_sort_by_score_and_by_distance(self):
        with self.test_request_context():
            # 1) Search for `D1405` ROME code only. We should get 1 result.
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000004')
            self.assertEqual(data['companies'][0]['matched_rome_code'], 'D1405')

            # 2) Search for `M1801` ROME code only. We should get 1 result.
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'M1801',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000005')
            # matched_rome_* fields are useless for single rome searches but must still
            # be present for consistency from the point of view of the API user.
            self.assertEqual(data['companies'][0]['matched_rome_code'], 'M1801')
            self.assertIn('matched_rome_label', data['companies'][0])
            self.assertIn('matched_rome_slug', data['companies'][0])

            # 3) Multi rome search for both `D1405` and `M1801` ROME codes, sorting by distance.
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405,M1801',
                'user': 'labonneboite',
                'sort': 'distance',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            self.assertIn('matched_rome_code', data['companies'][0])
            self.assertIn('matched_rome_label', data['companies'][0])
            self.assertIn('matched_rome_slug', data['companies'][0])
            self.assertIn('matched_rome_code', data['companies'][1])
            self.assertIn('matched_rome_label', data['companies'][1])
            self.assertIn('matched_rome_slug', data['companies'][1])
            self.assertEqual(
                set([c['siret'] for c in data['companies']]),
                set(['00000000000004', '00000000000005'])
            )

            # 4) Multi rome search for both `D1405` and `M1801` ROME codes, sorting by score.
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405,M1801',
                'user': 'labonneboite',
                'sort': 'score',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            self.assertIn('matched_rome_code', data['companies'][0])
            self.assertIn('matched_rome_label', data['companies'][0])
            self.assertIn('matched_rome_slug', data['companies'][0])
            self.assertIn('matched_rome_code', data['companies'][1])
            self.assertIn('matched_rome_label', data['companies'][1])
            self.assertIn('matched_rome_slug', data['companies'][1])
            self.assertEqual(
                set([c['siret'] for c in data['companies']]),
                set(['00000000000004', '00000000000005'])
            )

    def test_wrong_naf_value(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': 'D1508',
                'naf_codes': 'INVALID,INVALID_TOO',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertTrue(rv.data.decode().startswith('Invalid request argument: NAF code(s): INVALID INVALID_TOO'))

    def test_same_rome_with_no_naf_filters(self):
        with self.test_request_context():
            # 1) No NAF Code => 2 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': 'D1508',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            self.assertNotEqual(data['companies'][0]['naf'], data['companies'][1]['naf'])

    def test_same_rome_with_one_naf_filters(self):
        with self.test_request_context():
            # 1) NAF Code : 4771Z => 1 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': 'D1508',
                'naf_codes': '4771Z',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000006')

            # 2) NAF Code : 4711F => 1 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': 'D1508',
                'naf_codes': '4711F',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000007')

    def test_same_rome_with_two_naf_filters(self):
        with self.test_request_context():
            # 1) NAF codes : 4711F,4771Z => 2 results expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': 'D1508',
                'naf_codes': '4711F,4771Z',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)

    def test_same_rome_with_unrelated_naf_filters(self):
        with self.test_request_context():
            # NAF Code : 9499Z => 0 result expected
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': 'D1508',
                'naf_codes': '9499Z',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertIn('Invalid request argument: NAF code(s): 9499Z. Possible values : ', rv.data.decode())

    def test_wrong_value_in_sort(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['nantes']['commune_id'],
                'rome_codes': 'D1211',
                'sort': 'INVALID',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'Invalid request argument: sort. Possible values : score, distance')

    def test_sort_by_distance(self):
        with self.test_request_context():
            # Nantes in first place, then Reze
            params = self.add_security_params({
                'commune_id': self.positions['nantes']['commune_id'],
                'rome_codes': 'D1211',
                'sort': 'distance',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            self.assertEqual(data["companies"][0]['siret'], '00000000000008')
            self.assertEqual(data["companies"][1]['siret'], '00000000000009')
            self.assertLess(data["companies"][0]['distance'], data["companies"][1]['distance'])

    def test_sort_by_score(self):
        with self.test_request_context():
            # Reze in first place, then Nantes
            params = self.add_security_params({
                'commune_id': self.positions['nantes']['commune_id'],
                'rome_codes': 'D1211',
                'sort': 'score',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set(['00000000000009', '00000000000008']))

    def test_wrong_contract_value(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['lille']['commune_id'],
                'rome_codes': 'D1213',
                'user': 'labonneboite',
                'contract': 'Invalid'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'Invalid request argument: contract. Possible values : alternance, dpae')

    def test_wrong_headcount_value(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': 'M1202',
                'user': 'labonneboite',
                'headcount': 'INVALID'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'Invalid request argument: headcount. Possible values : all, big, small')

    def test_headcount_all(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': 'M1202',
                'user': 'labonneboite',
                'headcount': 'all'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            self.assertEqual(len(data['companies']), 2)

    def test_headcount_small(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': 'M1202',
                'user': 'labonneboite',
                'headcount': 'small'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000012')
            self.assertEqual(data['companies'][0]['headcount_text'], '10 à 19 salariés')

    def test_headcount_big(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulouse']['commune_id'],
                'rome_codes': 'M1202',
                'user': 'labonneboite',
                'headcount': 'big'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000013')
            self.assertEqual(data['companies'][0]['headcount_text'], '100 à 199 salariés')

    def test_contact_mode(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(len(data['companies']), 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000004')
            self.assertEqual(data['companies'][0]['contact_mode'], 'Se présenter spontanément')

    def test_flag_alternance(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['poitiers']['commune_id'],
                'rome_codes': 'B1603',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            sirets = {c['siret']: c for c in data['companies']}
            self.assertEqual(sorted(sirets.keys()), ['00000000000015', '00000000000016'])
            self.assertFalse(sirets['00000000000015']['alternance'])
            self.assertTrue(sirets['00000000000016']['alternance'])

    def test_flag_pmsmp_filter_incorrect_value(self):
        with self.test_request_context():
            # Invalid flag_pmsmp filter => Expected error message
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'supertrusteduser', # needs to have access to pmsmp
                'flag_pmsmp': '18',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertIn(
                'Invalid request argument: flag_pmsmp must be boolean (0 or 1)',
                rv.data.decode(),
            )

    def test_flag_pmsmp_filter_get_all_companies(self):
        with self.test_request_context():
            # flag_pmsmp=0 (all companies) => Expected 2 results
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'supertrusteduser', # needs to have access to pmsmp
                'flag_pmsmp': '0',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set(['00000000000017', '00000000000018']))

    def test_flag_pmsmp_filter_silently_ignored_if_user_is_not_authorized(self):
        with self.test_request_context():
            # Unauthorized api user => flag_pmsmp=1 silently ignored, still getting 2 results
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'labonneboite',
                'flag_pmsmp': '1',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set(['00000000000017', '00000000000018']))

    def test_flag_pmsmp_filter_normal_behavior(self):
        with self.test_request_context():
            # no flag_pmsmp filter => Expected 2 results
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set(['00000000000017', '00000000000018']))

            # flag_pmsmp=1 (only pmsmp companies) => Expected 1 result
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'supertrusteduser', # needs to have access to pmsmp
                'flag_pmsmp': '1',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000017')

    def test_department_filters(self):
        with self.test_request_context():
            # Invalid departments filter => Expected error message
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'labonneboite',
                'departments': '75,XX,YY'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 400)
            self.assertIn('Invalid request argument: departments : XX, YY', rv.data.decode())

            # no departments filter => Expected 2 results
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'labonneboite'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set(['00000000000017', '00000000000018']))

            # Check two departments => Expected 2 results
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'labonneboite',
                'departments': '75,92'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 2)
            sirets = set([data['companies'][0]['siret'], data['companies'][1]['siret']])
            self.assertEqual(sirets, set(['00000000000017', '00000000000018']))

            # Check department 75 => Expected 1 result
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'labonneboite',
                'departments': '75'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000017')

            # Check department 92 => Expected 1 result
            params = self.add_security_params({
                'commune_id': self.positions['paris']['commune_id'],
                'rome_codes': 'N1202',
                'user': 'labonneboite',
                'departments': '92'
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['companies_count'], 1)
            self.assertEqual(data['companies'][0]['siret'], '00000000000018')

    def test_filters_in_api_response(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            # Check distance filter
            self.assertEqual(data['filters']['distance']['less_30_km'], 4)
            self.assertEqual(data['filters']['distance']['less_50_km'], 5)
            self.assertEqual(data['filters']['distance']['less_100_km'], 6)
            self.assertEqual(data['filters']['distance']['france'], 7)

            # Check naf filter
            nafs_expected = {
                '4910Z': ['4910Z', 2, 'Transport ferroviaire interurbain de voyageurs'],
                '4920Z': ['4920Z', 1, 'Transports ferroviaires de fret'],
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
            self.assertEqual(data['filters']['contract']['dpae'], 3)
            self.assertEqual(data['filters']['contract']['alternance'], 1)

    def test_filters_when_filtering_by_naf(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'naf_codes': '4910Z',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            nafs_expected = {
                '4910Z': ['4910Z', 2, 'Transport ferroviaire interurbain de voyageurs'],
                '4920Z': ['4920Z', 1, 'Transports ferroviaires de fret'],
            }
            self.assertEqual(len(nafs_expected), len(data['filters']['naf']))
            for naf_filter in data['filters']['naf']:
                naf_expected = nafs_expected[naf_filter['code']]
                self.assertEqual(naf_expected[0], naf_filter['code'])
                self.assertEqual(naf_expected[1], naf_filter['count'])
                self.assertEqual(naf_expected[2], naf_filter['label'])

    def test_filters_when_filtering_by_headcount(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'headcount': 'big',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['filters']['headcount']['small'], 2)
            self.assertEqual(data['filters']['headcount']['big'], 1)

            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'headcount': 'small',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['filters']['headcount']['small'], 2)
            self.assertEqual(data['filters']['headcount']['big'], 1)

    def test_filters_when_filtering_by_contract(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'contract': 'dpae',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['filters']['contract']['dpae'], 3)
            self.assertEqual(data['filters']['contract']['alternance'], 1)

            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'contract': 'alternance',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['filters']['contract']['dpae'], 3)
            self.assertEqual(data['filters']['contract']['alternance'], 1)

    def test_filters_when_filtering_by_distance(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'distance': '50',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            self.assertEqual(data['filters']['distance']['less_10_km'], 3)
            self.assertEqual(data['filters']['distance']['less_30_km'], 4)
            self.assertEqual(data['filters']['distance']['less_50_km'], 5)
            self.assertEqual(data['filters']['distance']['less_100_km'], 6)
            self.assertEqual(data['filters']['distance']['france'], 7)

            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'distance': '100',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_filter_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['filters']['distance']['less_10_km'], 3)
            self.assertEqual(data['filters']['distance']['less_30_km'], 4)
            self.assertEqual(data['filters']['distance']['less_50_km'], 5)
            self.assertEqual(data['filters']['distance']['less_100_km'], 6)
            self.assertEqual(data['filters']['distance']['france'], 7)

    def test_search_url_present_in_response(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'user': 'labonneboite',
            })

            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            self.assertTrue(data['companies_count'] >= 1)
            expect = '/entreprises/commune/{}/rome/{}'.format(self.positions['toulon']['commune_id'], 'N4403')
            self.assertIn(expect, data['url'])

    def test_search_url_preserves_original_parameters(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'user': 'labonneboite',
                # extra non default parameters
                # let's see if they are preserved
                'naf_codes': '4910Z',
                'sort': 'distance',
                'distance': 20,
            })

            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            self.assertTrue(data['companies_count'] >= 1)
            expect = '/entreprises/commune/{}/rome/{}'.format(self.positions['toulon']['commune_id'], 'N4403')
            self.assertIn(expect, data['url'])
            self.assertIn('naf=4910Z', data['url'])
            self.assertIn('sort=distance', data['url'])
            self.assertIn('d=20', data['url'])

    def test_home_url_instead_of_search_url_when_searching_with_coordinates(self):
        # FIXME at some point we should implement returning a URL with coordinates
        # but for now we just return the home URL
        with self.test_request_context():
            params = self.add_security_params({
                'latitude': self.positions['toulon']['coords'][0]['lat'],
                'longitude': self.positions['toulon']['coords'][0]['lon'],
                'rome_codes': 'N4403',
                'user': 'labonneboite',
            })

            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            # ensure we return home URL and not search URL
            self.assertNotIn('/entreprises', data['url'])
            self.assertIn(url_for("root.home", _external=True), data['url'])

    def test_empty_result_returns_home_url_instead_of_search_url(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['caen']['commune_id'],
                'distance': 20,
                'page': 1,
                'page_size': 2,
                'rome_codes': 'J1103',  # no office has this ROME code
                'user': 'labonneboite',
            })

            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            self.assertEqual(data['companies_count'], 0)
            self.assertEqual(len(data['companies']), 0)

            # ensure we return home URL and not search URL
            self.assertNotIn('/entreprises', data['url'])
            self.assertIn(url_for("root.home", _external=True), data['url'])

    def test_company_count_endpoint(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['toulon']['commune_id'],
                'rome_codes': 'N4403',
                'user': 'labonneboite',
            })

            rv = self.app.get(self.url_for("api.company_count", **params))
            self.assertEqual(rv.status_code, 200)
            data_count = json.loads(rv.data.decode())

            self.assertIn('companies_count', data_count)
            self.assertTrue(data_count['companies_count'] >= 1)
            self.assertNotIn('companies', data_count)

            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data_list = json.loads(rv.data.decode())

            self.assertIn('companies_count', data_list)
            self.assertEqual(data_list['companies_count'], data_count['companies_count'])
            self.assertIn('companies', data_list)

    def test_internal_user_call(self):
        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': 'D1405',
            'distance': '10',
            'user': 'untrusteduser',
        })

        response_unprivileged = self.app.get(self.url_for("api.company_list", **params))

        params = self.add_security_params({
            'commune_id': self.positions['caen']['commune_id'],
            'rome_codes': 'D1405',
            'distance': '10',
            'user': 'supertrusteduser', # needs to have access to pmsmp
        })

        response_privileged = self.app.get(self.url_for("api.company_list", **params))

        company_without_info = json.loads(response_unprivileged.data.decode())['companies'][0]
        company_with_info = json.loads(response_privileged.data.decode())['companies'][0]

        self.assertNotIn("email", company_without_info)
        self.assertNotIn("phone", company_without_info)
        self.assertNotIn("website", company_without_info)
        self.assertIn("email", company_with_info)
        self.assertIn("phone", company_with_info)
        self.assertIn("website", company_with_info)

    def test_romes_boost(self):
        with self.test_request_context():
            params = self.add_security_params({
                'contract': 'dpae',
                'longitude': self.positions['toulon']['coords'][0]['lon'],
                'latitude': self.positions['toulon']['coords'][0]['lat'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })

            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
    def test_romes_boost_alternance(self):
        with self.test_request_context():
            params = self.add_security_params({
                'contract': 'alternance',
                'longitude': self.positions['toulon']['coords'][0]['lon'],
                'latitude': self.positions['toulon']['coords'][0]['lat'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
            })

            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)

    def test_multiple_romes(self):
        # with mock.patch.object(settings, 'ALTERNANCE_SEARCH_MODE', 'xxx'):
            with self.test_request_context():
                params = self.add_security_params({
                    'contract': 'alternance',
                    'longitude': self.positions['toulon']['coords'][0]['lon'],
                    'latitude': self.positions['toulon']['coords'][0]['lat'],
                    'rome_codes': 'D1405,N4403',
                    'user': 'labonneboite',
                })

                rv = self.app.get(self.url_for("api.company_list", **params))
                self.assertEqual(rv.status_code, 200)


class ApiOffersOfficesListTest(ApiBaseTest):
    """
    Test the API route: `offers_offices_list`.
    """

    def test_happy_path(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['metz']['commune_id'],
                'rome_codes': 'D1212',
                'contract': 'alternance',
                'user': 'labonneboite',
                'distance': 50,
            })

            with mock.patch('labonneboite.common.esd.get_response', return_value=self.get_fixture('esd-offres-happypath.json')) as mock_response:
                rv = self.app.get(url_for("api.offers_offices_list", **params))
                mock_response.assert_called_once()

            self.assertEqual(rv.status_code, 200)
            result = json.loads(rv.data.decode())
            self.assertEqual(result['companies_count'], 5)
            self.assertEqual(len(result['companies']), 5)
            for office_json in result['companies']:
                self.assertIn('distance', office_json)
                self.assertIn('offers_count', office_json)
                self.assertTrue(office_json['offers_count'] >= 1)
                self.assertIn('offers', office_json)
                self.assertEqual(office_json['offers_count'], len(office_json['offers']))
                for offer_json in office_json['offers']:
                    self.assertIn('id', offer_json)
                    self.assertIn('name', offer_json)
                    self.assertIn('url', offer_json)

    def test_multi_rome_is_supported_single_batch(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['bayonville_sur_mad']['commune_id'],
                'rome_codes': 'D1405,D1507,D1212',
                'contract': 'alternance',
                'user': 'labonneboite',
                'distance': 50,
            })

            with mock.patch('labonneboite.common.esd.get_response', return_value=self.get_fixture('esd-offres-happypath.json')) as mock_response:
                rv = self.app.get(url_for("api.offers_offices_list", **params))
                # romes are batched by 3 - 3 romes is 1 batch
                mock_response.assert_called_once()

            self.assertEqual(rv.status_code, 200)
            result = json.loads(rv.data.decode())
            self.assertEqual(result['companies_count'], 5)
            self.assertEqual(len(result['companies']), 5)
            for office_json in result['companies']:
                self.assertIn('distance', office_json)
                self.assertIn('offers_count', office_json)
                self.assertIn('offers', office_json)

    def test_multi_rome_is_supported_multi_batch(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['bayonville_sur_mad']['commune_id'],
                'rome_codes': 'D1405,D1507,D1212,A1101',
                'contract': 'alternance',
                'user': 'labonneboite',
                'distance': 50,
            })

            with mock.patch('labonneboite.common.esd.get_response', return_value=self.get_fixture('esd-offres-happypath.json')) as mock_response:
                rv = self.app.get(url_for("api.offers_offices_list", **params))
                # romes are batched by 3 - 4 romes is 2 batches
                self.assertEqual(mock_response.call_count, 2)

            self.assertEqual(rv.status_code, 200)
            result = json.loads(rv.data.decode())
            self.assertEqual(result['companies_count'], 5)
            self.assertEqual(len(result['companies']), 5)
            for office_json in result['companies']:
                self.assertIn('distance', office_json)
                self.assertIn('offers_count', office_json)
                self.assertIn('offers', office_json)

    def test_dpae_scoring_not_supported(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['bayonville_sur_mad']['commune_id'],
                'rome_codes': 'D1405',
                'user': 'labonneboite',
                'distance': 50,
            })

            rv = self.app.get(url_for("api.offers_offices_list", **params))

            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'parameter contract is required', rv.data)

        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['bayonville_sur_mad']['commune_id'],
                'rome_codes': 'D1405',
                'contract': 'dpae',
                'user': 'labonneboite',
                'distance': 50,
            })

            rv = self.app.get(url_for("api.offers_offices_list", **params))

            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'only contract=alternance is supported', rv.data)

    def test_gps_search_not_supported(self):
        with self.test_request_context():
            params = self.add_security_params({
                'latitude': self.positions['bayonville_sur_mad']['coords'][0]['lat'],
                'longitude': self.positions['bayonville_sur_mad']['coords'][0]['lon'],
                'rome_codes': 'D1405',
                'contract': 'alternance',
                'user': 'labonneboite',
                'distance': 50,
            })

            rv = self.app.get(url_for("api.offers_offices_list", **params))

            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'parameter longitude is not supported', rv.data)

    def test_pagination_not_supported(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['bayonville_sur_mad']['commune_id'],
                'rome_codes': 'D1405',
                'contract': 'alternance',
                'user': 'labonneboite',
                'distance': 50,
                'page': 2,
            })

            rv = self.app.get(url_for("api.offers_offices_list", **params))

            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'only page=1 is supported as pagination is not implemented', rv.data)


class ApiCompanyListTrackingCodesTest(ApiBaseTest):

    def assertTrackingCodesEqual(self, company_url, utm_medium, utm_source, utm_campaign):
        url_query = urllib.parse.urlparse(company_url)[4]
        url_params = urllib.parse.parse_qs(url_query)

        self.assertIn('utm_medium', url_params)
        self.assertEqual([utm_medium], url_params.get('utm_medium'))
        self.assertIn('utm_source', url_params)
        self.assertEqual([utm_source], url_params.get('utm_source'))
        self.assertIn('utm_campaign', url_params)
        self.assertEqual([utm_campaign], url_params.get('utm_campaign'))

    def test_api_urls_include_google_analytics_tracking(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['pau']['commune_id'],
                'distance': 10,
                'rome_codes': 'B1603',
                'user': 'labonneboite',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            company_url = data['companies'][0]['url']

        self.assertTrackingCodesEqual(company_url, 'web', 'api__labonneboite', 'api__labonneboite')

    def test_api_urls_include_google_analytics_tracking_with_origin_user(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['pau']['commune_id'],
                'distance': 10,
                'rome_codes': 'B1603',
                'user': 'labonneboite',
                'origin_user': 'someuser',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            company_url = data['companies'][0]['url']
            self.assertTrackingCodesEqual(company_url, 'web', 'api__labonneboite', 'api__labonneboite__someuser')

    def test_google_analytics_for_labonneboite_search_url(self):
        with self.test_request_context():
            params = self.add_security_params({
                'commune_id': self.positions['pau']['commune_id'],
                'distance': 10,
                'rome_codes': 'B1603',
                'user': 'labonneboite',
                'origin_user': 'someuser',
            })
            rv = self.app.get(self.url_for("api.company_list", **params))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())

            company_url = data['url']
            self.assertTrackingCodesEqual(company_url, 'web', 'api__labonneboite', 'api__labonneboite__someuser')
