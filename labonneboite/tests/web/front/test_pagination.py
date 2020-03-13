import unittest

from labonneboite.common.pagination import OFFICES_PER_PAGE, Page, PaginationManager


class PaginationTest(unittest.TestCase):
    def test_pagination_one_page(self):
        company_count = 6
        pm = PaginationManager(company_count, 1, OFFICES_PER_PAGE, "")
        pm.get_pages()
        self.assertEqual(1, pm.get_page_count())

    def test_pagination_two_pages(self):
        company_count = 2 * OFFICES_PER_PAGE
        pm = PaginationManager(company_count, 1, OFFICES_PER_PAGE, "")
        pm.get_pages()
        self.assertEqual(2, pm.get_page_count())


class PageTest(unittest.TestCase):
    def test_unicode_query_parameter(self):
        original_url = "/pouac?h=1l%C3%A0"  # h=1là (observed in production)
        page = Page(1, 1, 1, original_url)
        self.assertEqual("/pouac?from=21&h=1l%C3%A0&to=1", page.get_url())

    def test_page_url_is_unicode(self):
        original_url = "/nîmes"  # (observed in production)
        page = Page(1, 1, 1, original_url)
        self.assertEqual("/nîmes?from=21&to=1", page.get_url())
