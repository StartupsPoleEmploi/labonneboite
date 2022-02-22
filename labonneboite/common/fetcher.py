from typing import Sequence

from labonneboite.common.models import OfficeResult


class InvalidFetcherArgument(Exception):
    pass


class Fetcher(object):
    office_count: int

    def get_offices(self) -> Sequence[OfficeResult]:
        raise NotImplementedError()

    def get_office_count(self) -> int:
        return self.office_count
