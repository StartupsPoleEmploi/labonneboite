import os
import errno
import logging

from labonneboite.conf import settings

logger = logging.getLogger('main')


def get_file_path(office):
    file_path = "pdf/%s/%s/%s/%s.pdf" % (office.departement, office.naf, office.name.strip()[0], office.siret)
    full_path = os.path.join(settings.GLOBAL_STATIC_PATH, file_path)
    return full_path


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
