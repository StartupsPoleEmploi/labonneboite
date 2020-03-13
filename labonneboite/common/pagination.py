import urllib.parse
from math import ceil
from urllib.parse import urlencode


OFFICES_PER_PAGE = 20  # constant for Frontend, variable default for API
OFFICES_MAXIMUM_PAGE_SIZE = 100  # API only as of now
FAVORITES_PER_PAGE = 10

# Has no real impact, only cosmetic impact on frontend, to avoid showing too many links
# at the same time in the search footer paginator in case they are hundreds of pages.
# All hundreds of pages are still perfectly browsable.
MAX_PAGES = 10


class Pagination(object):
    """
    A generic pagination class.
    """

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def pages_range(self):
        offset = 2
        min_ = max(1, self.page - offset)
        max_ = min(self.pages, self.page + offset)
        return list(range(min_, max_ + 1))

    @property
    def show_first(self):
        return 1 not in self.pages_range

    @property
    def show_first_ellipsis(self):
        return self.pages_range[0] != 2

    @property
    def show_last(self):
        return self.pages not in self.pages_range

    @property
    def show_last_ellipsis(self):
        return self.pages_range[-1] != (self.pages - 1)


class PaginationManager(object):
    """
    Specific pagination class for office search results.
    """

    def __init__(self, company_count, current_from_number, current_to_number, full_path_url):
        self.pages = []
        self.company_count = company_count
        self.current_from_number = current_from_number
        self.current_to_number = current_to_number
        self.full_path_url = full_path_url
        self._current_page = None

    def _run(self):
        min_page, max_page = self.get_lower_and_upper_pages()
        for ranking in range(min_page, max_page):
            page = self._get_page(ranking)
            self.pages.append(page)

    def should_show(self):
        pages = self.get_pages()
        return len(pages) > 1

    def get_lower_and_upper_pages(self):
        page_count = self.get_page_count()
        current_page = self.get_current_page()

        if current_page < int(MAX_PAGES / 2) + 1:
            min_page = 0
            max_page = min(MAX_PAGES, page_count)
        else:
            max_page = min(current_page + int(MAX_PAGES / 2), page_count)
            if max_page == page_count:
                min_page = max(1, page_count - MAX_PAGES)
            else:
                min_page = max(0, current_page - int(MAX_PAGES / 2) - 1)
        return min_page, max_page

    def get_current_page(self):
        if not self._current_page:
            self._current_page = 1 + int(self.current_from_number / OFFICES_PER_PAGE)
        return self._current_page

    def get_page_count(self):
        return 1 + (self.company_count - 1) // OFFICES_PER_PAGE

    def get_pages(self):
        if not self.pages:
            self._run()
        return self.pages

    def show_first_page(self):
        min_page, _ = self.get_lower_and_upper_pages()
        return min_page > 1

    def show_last_page(self):
        _, max_page = self.get_lower_and_upper_pages()
        return max_page < self.get_page_count()

    def get_first_page(self):
        return self._get_page(0)

    def get_last_page(self):
        return self._get_page(self.get_page_count() - 1)

    def _get_page(self, ranking):
        return Page(ranking, self.company_count, self.current_from_number, self.full_path_url)


class Page(object):
    def __init__(self, ranking, company_count, current_from_number, original_url):
        """
        Args:
            ranking (int)
            company_count (int)
            current_from_number (int)
            original_url (unicode)
        """
        self.ranking = ranking
        self.company_count = company_count
        self._from_number = None
        self._to_number = None
        self.current_from_number = current_from_number
        self.url_parts = list(urllib.parse.urlparse(original_url))

    def get_from_number(self):
        if not self._from_number:
            self._from_number = 1 + self.ranking * OFFICES_PER_PAGE
        return self._from_number

    def get_to_number(self):
        if not self._to_number:
            self._to_number = min((self.ranking + 1) * OFFICES_PER_PAGE, self.company_count)
        return self._to_number

    def is_active(self):
        return self.get_from_number() == self.current_from_number

    def get_url(self):
        """
        Returns:
            page_url (unicode)
        """
        params = {"from": self.get_from_number(), "to": self.get_to_number()}
        url_query = dict(urllib.parse.parse_qsl(self.url_parts[4]))
        url_query.update(params)
        self.url_parts[4] = urlencode(sorted(url_query.items()))
        page_url = urllib.parse.urlunparse(self.url_parts)
        return page_url
