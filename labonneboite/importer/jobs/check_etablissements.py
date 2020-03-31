import sys
import os

from labonneboite.importer import util as import_util
from labonneboite.importer.util import history_importer_job_decorator


class NoDataException(Exception):
    pass


@history_importer_job_decorator(os.path.basename(__file__))
def run():
    filename = import_util.detect_runnable_file("etablissements")
    if not filename:
        raise NoDataException

if __name__ == '__main__':
    run()
