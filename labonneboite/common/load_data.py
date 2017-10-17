import os
import pickle
import csv

from backports.functools_lru_cache import lru_cache


def load_file(func, filename):
    full_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/%s" % filename)
    return func(full_filename)


def load_pickle_file(filename):
    def f(full_filename):
        return pickle.load(open(full_filename, "r"))
    return load_file(f, filename)


def load_csv_file(filename, delimiter=','):
    def f(full_filename):
        csv_file = open(full_filename, 'rb')
        reader = csv.reader(csv_file, delimiter=delimiter)
        return reader

    reader = load_file(f, filename)
    rows = []
    len_previous_row = None

    for row in reader:
        if len_previous_row:
            if len(row) != len_previous_row:
                raise Exception("found rows with different number of fields : %s" % row)
        rows.append(row)
        len_previous_row = len(row)

    return rows


@lru_cache(maxsize=None)
def load_city_codes():
    return load_pickle_file("city_codes_v2.pickle")


@lru_cache(maxsize=None)
def load_contact_modes():
    return load_pickle_file("contact_modes.pickle")


@lru_cache(maxsize=None)
def load_ogr_labels():
    rows = load_csv_file("ogr_labels.csv", delimiter=';')

    OGR_COLUMN = 0
    LABEL_COLUMN = 1
    ogr_to_label = {}

    for row in rows:
        ogr_to_label[row[OGR_COLUMN]] = row[LABEL_COLUMN].decode('utf8')

    return ogr_to_label


@lru_cache(maxsize=None)
def load_ogr_rome_mapping():
    rows = load_csv_file("ogr_rome_mapping.csv")

    OGR_COLUMN = 0
    ROME_COLUMN = 1
    ogr_to_rome = {}

    for row in rows:
        ogr = row[OGR_COLUMN]
        if ogr not in load_ogr_labels():
            raise Exception("missing label for OGR %s" % ogr)

        rome = row[ROME_COLUMN]
        if rome not in load_rome_labels():
            raise Exception("missing label for ROME %s" % rome)

        ogr_to_rome[ogr] = rome

    return ogr_to_rome


@lru_cache(maxsize=None)
def load_rome_labels():
    rows = load_csv_file("rome_labels.csv", delimiter=';')

    ROME_COLUMN = 0
    LABEL_COLUMN = 1
    rome_to_label = {}

    for row in rows:
        rome_to_label[row[ROME_COLUMN]] = row[LABEL_COLUMN].decode('utf8')

    return rome_to_label


@lru_cache(maxsize=None)
def load_naf_labels():
    # use pipe delimiter because ';' appear in label data
    rows = load_csv_file("naf_labels.csv", delimiter='|')

    NAF_COLUMN = 0
    LABEL_COLUMN = 1
    naf_to_label = {}

    for row in rows:
        naf_to_label[row[NAF_COLUMN]] = row[LABEL_COLUMN].decode('utf8')

    return naf_to_label


@lru_cache(maxsize=None)
def load_rome_naf_mapping():
    return load_csv_file("rome_naf_mapping.csv")



