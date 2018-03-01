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

    def test_error_if_invalid_job_slug(self):
        with self.test_request_context:
            rv = self.app.get('{}?job-slug={}'.format(
                url_for("search.job_slug_details"),
                'INVALID_SLUG',
            ))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, 'no rome found associated to the slug INVALID_SLUG')

    def test_error_if_invalid_city_slugs(self):
        with self.test_request_context:
            rv = self.app.get('{}?city-slug={}'.format(
                url_for("search.city_slug_details"),
                'INVALID_SLUG',
            ))
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, 'no city found associated to the slug INVALID_SLUG')

    def test_ok_job_slug(self):
        with self.test_request_context:
            rv = self.app.get('{}?job-slug={}'.format(
                url_for("search.job_slug_details"),
                'abattage-et-decoupe-des-viandes',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['job']['label'], u'Abattage et découpe des viandes')
            self.assertEqual(data['job']['rome_code'], u'H2101')

    def test_ok_city_slug(self):
        with self.test_request_context:
            rv = self.app.get('{}?city-slug={}'.format(
                url_for("search.city_slug_details"),
                'nantes-44000',
            ))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data)
            self.assertEqual(data['city']['name'], u'Nantes')
            self.assertEqual(data['city']['latitude'], 47.235456880128645)
            self.assertEqual(data['city']['longitude'], -1.5498348824858057)
