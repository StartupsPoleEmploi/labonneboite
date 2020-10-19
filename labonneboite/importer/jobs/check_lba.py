import os

from labonneboite.importer import util as import_util
from labonneboite.importer.util import history_importer_job_decorator


class NoDataException(Exception):
    pass


@history_importer_job_decorator(os.path.basename(__file__))
def run():
    filename_apprentissage = import_util.detect_runnable_file("lba-app")
    filename_contrat_pro = import_util.detect_runnable_file("lba-pro")
    if not filename_apprentissage or not filename_contrat_pro:
        raise NoDataException


if __name__ == '__main__':
    run()
