# coding: utf8
from labonneboite.tests.test_base import AppTest


class HealthTest(AppTest):

    def test_health(self):
        rv = self.app.get("/health")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, b'yes')

        rv = self.app.get("/health/db")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, b'yes')

        rv = self.app.get("/health/es")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, b'yes')
