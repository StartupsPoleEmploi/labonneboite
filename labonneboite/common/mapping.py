# coding: utf8

import logging

from labonneboite.common.load_data import load_ogr_rome_codes, load_manual_rome_naf_file
from labonneboite.conf import settings
from slugify import slugify

logger = logging.getLogger('main')

OGR_ROME_CODES = load_ogr_rome_codes()
ROME_CODES = OGR_ROME_CODES.values()
SLUGIFIED_ROME_LABELS = {slugify(v): k for k, v in settings.ROME_DESCRIPTIONS.items()}

# these variables will be populated once by load_manual_rome_naf_mapping()
NAF_CODES_FROM_ROME_NAF_MAPPING = set()
MANUAL_ROME_NAF_MAPPING = {}
MANUAL_NAF_ROME_MAPPING = {}

def load_manual_rome_naf_mapping():
    reader = load_manual_rome_naf_file()

    ROME_COLUMN = 0
    NAF_COLUMN = 2
    HIRINGS_COLUMN = 4

    for columns in reader:

        rome = columns[ROME_COLUMN].strip().upper()
        naf = columns[NAF_COLUMN].strip().upper()
        hirings = int(columns[HIRINGS_COLUMN].strip())

        MANUAL_ROME_NAF_MAPPING.setdefault(rome, {})
        if naf not in MANUAL_ROME_NAF_MAPPING[rome]:
            MANUAL_ROME_NAF_MAPPING[rome][naf] = hirings
        else:
            raise Exception("duplicate mapping")

        MANUAL_NAF_ROME_MAPPING.setdefault(naf, {})
        if rome not in MANUAL_NAF_ROME_MAPPING[naf]:
            MANUAL_NAF_ROME_MAPPING[naf][rome] = hirings
        else:
            raise Exception("duplicate mapping")

        NAF_CODES_FROM_ROME_NAF_MAPPING.add(naf)


load_manual_rome_naf_mapping()  # populates once all variables above


def load_rome_codes_from_rome_naf_mapping():
    return MANUAL_ROME_NAF_MAPPING.keys()


def load_naf_codes_from_rome_naf_mapping():
    #  the '[]' is the second parameter to 'sum' and allows for one line concatenating of a list of lists
    return set(sum((MANUAL_ROME_NAF_MAPPING[rome].keys() for rome in MANUAL_ROME_NAF_MAPPING.keys()), []))


class Rome2NafMapper(object):

    def __init__(self):
        self.rome_2_naf_dict = MANUAL_ROME_NAF_MAPPING

    def map(self, rome_codes, optional_naf_codes=None):
        naf_codes = set()
        for rome in rome_codes:
            if rome not in ROME_CODES:
                raise Exception('bad rome code %s' % rome)
            try:
                naf_codes_with_hirings = self.rome_2_naf_dict[rome]
            except KeyError:
                logger.error('soft fail: no NAF codes for ROME %s', rome)
                naf_codes_with_hirings = {}
            for naf, _ in naf_codes_with_hirings.iteritems():
                if optional_naf_codes:
                    if naf in optional_naf_codes:
                        naf_codes.add(naf)
                else:
                    naf_codes.add(naf)
        return list(naf_codes)
