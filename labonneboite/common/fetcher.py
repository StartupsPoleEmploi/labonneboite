class InvalidFetcherArgument(Exception):
    pass


class Fetcher(object):
    def get_offices(self):
        raise NotImplementedError()

    def get_office_count(self):
        return self.office_count
