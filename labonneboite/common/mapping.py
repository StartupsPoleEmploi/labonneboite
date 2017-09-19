# coding: utf8

from collections import namedtuple
import logging

from slugify import slugify

from labonneboite.common.load_data import load_ogr_rome_codes, load_manual_rome_naf_file
from labonneboite.conf import settings
from labonneboite.conf.common.naf_codes import NAF_CODES


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

    def romes_for_naf(self, naf):
        """
        Returns ROME codes matching the given NAF code as a list of named tuples ordered by the number of hires.
        E.g. for NAF 4212Z:
        [
            Rome(code='F1702', name=u'Construction de routes et voies', nafs={'4212Z': 395, '8130Z': 112}),
            Rome(code='F1201', name=u'Conduite de travaux du BTP', nafs={'4212Z': 86, '7810Z': 17}),
            Rome(code='N4403', name=u'Manoeuvre du réseau ferré', nafs={'4910Z': 12, '4920Z': 8}),
            ...
        ]
        """
        romes_for_naf = {k: v for (k, v) in self.rome_2_naf_dict.items() if naf in v}
        romes_for_naf = sorted(romes_for_naf.items(), key=lambda (k, v): v[naf], reverse=True)
        Rome = namedtuple('Rome', ['code', 'name', 'nafs'])
        return [Rome(rome[0], settings.ROME_DESCRIPTIONS[rome[0]], rome[1]) for rome in romes_for_naf]

    def nafs_for_rome(self, rome):
        """
        Returns NAF codes matching the given ROME code as a list of named tuples ordered by the number of hires.
        E.g. for ROME M1607:
        [
            Naf(code='8810A', name=u'Aide à domicile', hirings=2830),
            Naf(code='6831Z', name=u'Agences immobilières', hirings=897),
            Naf(code='8422Z', name=u'Défense', hirings=6),
            ...
        ]
        """
        nafs = self.rome_2_naf_dict.get(rome, {})
        nafs = sorted(nafs.items(), key=lambda (k, v): v, reverse=True)
        Naf = namedtuple('Naf', ['code', 'name', 'hirings'])
        return [Naf(naf[0], NAF_CODES[naf[0]], naf[1]) for naf in nafs]

    @staticmethod
    def romes_is_valid(rome):
        """
        Returns True if the given ROME code is valid, False otherwise.
        """
        return rome in settings.ROME_DESCRIPTIONS

    @staticmethod
    def naf_is_valid(naf):
        """
        Returns True if the given NAF code is valid, False otherwise.
        """
        return naf in NAF_CODES
