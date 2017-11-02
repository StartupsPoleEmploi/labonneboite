# coding: utf8
import unittest

from labonneboite.web.pagination import Page, PaginationManager


class PaginationTest(unittest.TestCase):

    def test_pagination_one_page(self):
        company_count = 6
        pm = PaginationManager(company_count, 1, 10, "")
        pm.get_pages()
        self.assertEquals(1, pm.get_page_count())

    def test_pagination_two_pages(self):
        company_count = 20
        pm = PaginationManager(company_count, 1, 10, "")
        pm.get_pages()
        self.assertEquals(2, pm.get_page_count())


class PageTest(unittest.TestCase):

    def test_unicode_url(self):
        original_url = u'/pouac?h=1l%C3%A0' # h=1là (observed in production)
        page = Page(1, 1, 1, original_url)
        self.assertEqual('/pouac?h=1l%C3%A0&from=11&to=1', page.get_url())
