from typing import Sequence, Tuple, Optional, Dict, Union

from labonneboite.common.models import OfficeResult


class InvalidFetcherArgument(Exception):
    pass


AggregationType = Union[Dict, Sequence[Dict]]
AggregationsType = Dict[str, AggregationType]


class Fetcher(object):
    office_count: int

    def get_offices(self, add_suggestions: bool = ...) -> Tuple[Sequence[OfficeResult], Optional[AggregationsType]]:
        raise NotImplementedError()

    def get_office_count(self) -> int:
        return self.office_count
