# coding: utf8

from collections import namedtuple
import logging

from slugify import slugify

from labonneboite.common.load_data import load_rome_naf_mapping
from labonneboite.conf import settings


logger = logging.getLogger('main')


SLUGIFIED_ROME_LABELS = {slugify(v): k for k, v in settings.ROME_DESCRIPTIONS.items()}

# these variables will be populated once by load_manual_rome_naf_mapping()
MANUAL_ROME_NAF_MAPPING = {}
MANUAL_NAF_ROME_MAPPING = {}

ENSURE_LABELS_IN_MAPPING_MATCH = False  # FIXME resolve pending issue of non matching label data


def populate_rome_naf_mapping():
    rows = load_rome_naf_mapping()

    ROME_COLUMN = 0
    ROME_LABEL_COLUMN = 1
    NAF_COLUMN = 2
    NAF_LABEL_COLUMN = 3
    HIRINGS_COLUMN = 4

    for row in rows:

        rome = row[ROME_COLUMN].strip().upper()
        rome_label = row[ROME_LABEL_COLUMN]
        naf = row[NAF_COLUMN].strip().upper()
        naf_label = row[NAF_LABEL_COLUMN]
        hirings = int(row[HIRINGS_COLUMN].strip())

        if rome not in settings.ROME_DESCRIPTIONS:
            raise Exception("missing label for ROME %s" % rome)

        if naf not in settings.NAF_CODES:
            raise Exception("missing label for NAF %s" % naf)

        if ENSURE_LABELS_IN_MAPPING_MATCH:

            if naf_label != settings.NAF_CODES[naf].encode('utf8'):
                raise Exception("labels '%s' and '%s' do not match for NAF %s" % (
                    naf_label,
                    settings.NAF_CODES[naf].encode('utf8'),
                    naf,
                    )
                )

            if rome_label != settings.ROME_DESCRIPTIONS[rome].encode('utf8'):
                raise Exception("labels '%s' and '%s' do not match for ROME %s" % (
                    rome_label,
                    settings.ROME_DESCRIPTIONS[rome].encode('utf8'),
                    rome,
                    )
                )

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


populate_rome_naf_mapping()  # populates once all variables above


class Rome2NafMapper(object):

    def __init__(self):
        self.rome_2_naf_dict = MANUAL_ROME_NAF_MAPPING

    def map(self, rome_codes, optional_naf_codes=None):
        naf_codes = set()
        for rome in rome_codes:
            if rome not in settings.ROME_DESCRIPTIONS.keys():
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
        return [Naf(naf[0], settings.NAF_CODES[naf[0]], naf[1]) for naf in nafs]

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
        return naf in settings.NAF_CODES
