# coding: utf8
import unittest

from labonneboite.web.pagination import PaginationManager


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
