# coding: utf8
import errno
import logging
import os

from slugify import slugify

from labonneboite.conf import settings

logger = logging.getLogger('main')


def get_file_path(office):
    return os.path.join(settings.GLOBAL_STATIC_PATH, "pdf",
                        office.departement, office.naf, slugify(office.name.strip()[0]),
                        "%s.pdf" % office.siret)


def write_file(office, data):
    filename = get_file_path(office)
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:
            # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, "w") as f:
        f.write(data)
    f.close()
    logger.info("wrote PDF file to %s", filename)


def delete_file(office):
    filename = get_file_path(office)
    if os.path.exists(filename):
        os.remove(filename)
