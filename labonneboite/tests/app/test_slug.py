# coding: utf8
import json, unittest

from flask import url_for
from labonneboite.tests.test_base import AppTest

class SlugDetailsTest(AppTest):

    def test_error_if_no_slug(self):
        with self.test_request_context:
            # Job slug
            rv = self.app.get('{}'.format(url_for("search.job_slug_details")))
            self.assertEqual(rv.status_code, 400)

            # City slug
            rv = self.app.get('{}'.format(url_for("search.city_slug_details")))
            self.assertEqual(rv.status_code, 400)

    def test_error_if_invalid_city_slugs(self):
        with self.test_request_context:
            rv = self.app.get('{}?city-slug={}'.format(
                url_for("search.city_slug_details"),
                'INVALID_SLUG',
            ))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'no city found associated to the slug INVALID_SLUG')

    def test_ok_job_slug(self):
        with self.test_request_context:
            rv = self.app.get('{}?job-slug={}'.format(
                url_for("search.job_slug_details"),
                'abattage-et-decoupe-des-viandes',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data[0]['label'], 'Abattage et découpe des viandes')
            self.assertEqual(data[0]['rome_code'], 'H2101')

    def test_ok_multiple_job_slug(self):
        with self.test_request_context:
            rv = self.app.get('{}?job-slug={}'.format(
                url_for("search.job_slug_details"),
                'maconnerie,realisation-et-restauration-de-facades,construction-en-beton',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data[0]['rome_code'], 'F1703')
            self.assertEqual(data[0]['label'], 'Maçonnerie')
            self.assertEqual(data[1]['rome_code'], 'F1611')
            self.assertEqual(data[1]['label'], 'Réalisation et restauration de façades')
            self.assertEqual(data[2]['rome_code'], 'F1701')
            self.assertEqual(data[2]['label'], 'Construction en béton')

    def test_ignore_invalid_slug(self):
        with self.test_request_context:
            rv = self.app.get('{}?job-slug={}'.format(
                url_for("search.job_slug_details"),
                'maconnerie,INVALID_SLUG,realisation-et-restauration-de-facades',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['rome_code'], 'F1703')
            self.assertEqual(data[0]['label'], 'Maçonnerie')
            self.assertEqual(data[1]['rome_code'], 'F1611')
            self.assertEqual(data[1]['label'], 'Réalisation et restauration de façades')

    def test_empty_list_if_invalid_slugs(self):
        with self.test_request_context:
            rv = self.app.get('{}?job-slug={}'.format(
                url_for("search.job_slug_details"),
                'INVALID_SLUG_1,INVALID_SLUG_2',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(len(data), 0)

    def test_ok_city_slug(self):
        with self.test_request_context:
            rv = self.app.get('{}?city-slug={}'.format(
                url_for("search.city_slug_details"),
                'nantes-44000',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['city']['name'], 'Nantes')
            self.assertEqual(data['city']['latitude'], 47.235456880128645)
            self.assertEqual(data['city']['longitude'], -1.5498348824858057)


class CityCodeDetailsTest(AppTest):

    def test_ok_city_code(self):
        with self.test_request_context:
            rv = self.app.get('{}?city-code={}'.format(
                url_for("search.city_code_details"),
                '44109',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode())
            self.assertEqual(data['city']['name'], 'Nantes')
            self.assertEqual(data['city']['slug'], 'nantes-44000')
            self.assertEqual(data['city']['latitude'], 47.235456880128645)
            self.assertEqual(data['city']['longitude'], -1.5498348824858057)


    def test_error_if_invalid_city_code(self):
        with self.test_request_context:
            rv = self.app.get('{}?city-code={}'.format(
                url_for("search.city_code_details"),
                'INVALID_CODE',
            ))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'no city found associated to the code INVALID_CODE')
