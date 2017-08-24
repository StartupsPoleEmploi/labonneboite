# coding: utf8
from labonneboite.tests.test_base import AppTest


class StaticPagesTest(AppTest):

    def test_homepage(self):
        rv = self.app.get("/")
        self.assertEqual(rv.status_code, 200)

    def test_conditions_generales(self):
        rv = self.app.get("/conditions-generales")
        self.assertEqual(rv.status_code, 200)

    def test_faq(self):
        rv = self.app.get("/faq")
        self.assertEqual(rv.status_code, 200)

    def test_help(self):
        rv = self.app.get("/comment-faire-une-candidature-spontanee")
        self.assertEqual(rv.status_code, 200)

    def test_press(self):
        rv = self.app.get("/espace-presse")
        self.assertEqual(rv.status_code, 200)

    def test_cookbook(self):
        rv = self.app.get("/cookbook")
        self.assertEqual(rv.status_code, 200)

    def test_non_existing_page(self):
        rv = self.app.get("/this_page_does_not_exist")
        self.assertEqual(rv.status_code, 404)
