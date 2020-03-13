import logging
from collections import namedtuple
from functools import lru_cache

from slugify import slugify

from labonneboite.common.load_data import load_rome_naf_mapping
from labonneboite.conf import settings


logger = logging.getLogger("main")


SLUGIFIED_ROME_LABELS = {slugify(v): k for k, v in list(settings.ROME_DESCRIPTIONS.items())}

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

            if naf_label != settings.NAF_CODES[naf].encode("utf8"):
                raise Exception(
                    "labels '%s' and '%s' do not match for NAF %s"
                    % (naf_label, settings.NAF_CODES[naf].encode("utf8"), naf)
                )

            if rome_label != settings.ROME_DESCRIPTIONS[rome].encode("utf8"):
                raise Exception(
                    "labels '%s' and '%s' do not match for ROME %s"
                    % (rome_label, settings.ROME_DESCRIPTIONS[rome].encode("utf8"), rome)
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


@lru_cache(maxsize=1024)
def get_romes_for_naf(naf):
    return list(MANUAL_NAF_ROME_MAPPING[naf].keys())


@lru_cache(maxsize=1024)
def get_total_naf_hirings(naf):
    romes = get_romes_for_naf(naf)
    return sum(MANUAL_NAF_ROME_MAPPING[naf][rome] for rome in romes)


@lru_cache(maxsize=32 * 1024)
def get_affinity_between_rome_and_naf(rome_code, naf_code):
    """
    Ratio of hirings of this NAF made by this ROME.
    """
    current_rome_hirings = MANUAL_NAF_ROME_MAPPING[naf_code][rome_code]
    total_naf_hirings = get_total_naf_hirings(naf_code)

    if not (current_rome_hirings >= 1 and current_rome_hirings <= total_naf_hirings):
        raise Exception("error in hiring data for rome_code=%s and naf_code=%s" % (rome_code, naf_code))

    # 1.0 used to force float result, otherwise int/int like 30/100 give... zero
    return 1.0 * current_rome_hirings / total_naf_hirings


def map_romes_to_nafs(rome_codes, optional_naf_codes=None):
    naf_codes = set()
    for rome in rome_codes:
        if rome not in settings.ROME_DESCRIPTIONS:
            raise ValueError("bad rome code : %s" % rome)
        try:
            naf_codes_with_hirings = MANUAL_ROME_NAF_MAPPING[rome]
        except KeyError:
            logger.error("soft fail: no NAF codes for ROME %s", rome)
            naf_codes_with_hirings = {}
        for naf, _ in naf_codes_with_hirings.items():
            if optional_naf_codes:
                if naf in optional_naf_codes:
                    naf_codes.add(naf)
            else:
                naf_codes.add(naf)
    return list(naf_codes)


@lru_cache(maxsize=1024)  # about 700 naf_codes
def romes_for_naf(naf):
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
    romes = {k: v for (k, v) in list(MANUAL_ROME_NAF_MAPPING.items()) if naf in v}
    romes = sorted(list(romes.items()), key=lambda k_v: k_v[1][naf], reverse=True)
    Rome = namedtuple("Rome", ["code", "name", "nafs"])
    return [Rome(rome[0], settings.ROME_DESCRIPTIONS[rome[0]], rome[1]) for rome in romes]


@lru_cache(maxsize=8 * 1024)  # about 500 rome_codes in current dataset and 5000 in sliced dataset
def nafs_for_rome(rome):
    """
    Returns NAF codes matching the given ROME code as a list of named tuples ordered by the number of hires.
    E.g. for ROME M1607:
    [
        Naf(code='8810A', name=u'Aide à domicile', hirings=2830, affinity=0.04),
        Naf(code='6831Z', name=u'Agences immobilières', hirings=897, affinity=0.08),
        Naf(code='8422Z', name=u'Défense', hirings=6, affinity=0.20),
        ...
    ]
    """
    nafs = MANUAL_ROME_NAF_MAPPING.get(rome, {})
    nafs = sorted(list(nafs.items()), key=lambda k_v1: k_v1[1], reverse=True)
    Naf = namedtuple("Naf", ["code", "name", "hirings", "affinity"])
    return [
        Naf(naf[0], settings.NAF_CODES[naf[0]], naf[1], get_affinity_between_rome_and_naf(rome, naf[0]))
        for naf in nafs
    ]


def rome_is_valid(rome):
    """
    Returns True if the given ROME code is valid, False otherwise.
    """
    return rome in settings.ROME_DESCRIPTIONS


def naf_is_valid(naf):
    """
    Returns True if the given NAF code is valid, False otherwise.
    """
    return naf in settings.NAF_CODES
