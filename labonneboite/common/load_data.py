import os
import pickle
import csv

from backports.functools_lru_cache import lru_cache

USE_ROME_SLICING_DATASET = False  # Rome slicing dataset is not ready yet

if USE_ROME_SLICING_DATASET:
    OGR_ROME_FILE = "rome_slicing_dataset/ogr_rome_mapping.csv"
    ROME_FILE = "rome_slicing_dataset/rome_labels.csv"
    ROME_NAF_FILE = "rome_slicing_dataset/rome_naf_mapping.csv"
else:
    OGR_ROME_FILE = "ogr_rome_mapping.csv"
    ROME_FILE = "rome_labels.csv"
    ROME_NAF_FILE = "rome_naf_mapping.csv"


def load_file(func, filename):
    full_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/%s" % filename)
    return func(full_filename)


def load_pickle_file(filename):
    def f(full_filename):
        return pickle.load(open(full_filename, "r"))
    return load_file(f, filename)


def load_csv_file(filename, delimiter='|'):
    def f(full_filename):
        csv_file = open(full_filename, 'rb')
        reader = csv.reader(csv_file, delimiter=delimiter)
        return reader

    reader = load_file(f, filename)
    rows = []
    len_previous_row = None

    for row in reader:
        if len_previous_row:
            # at least second line of CSV file
            if len(row) != len_previous_row:
                raise Exception("found rows with different number of fields : %s" % row)
            rows.append(row)
        else:
            # first line of CSV file: headers should be ignored
            pass
        
        len_previous_row = len(row)

    return rows


def load_rows_as_dict(rows):
    d = {}
    for row in rows:
        if len(row) != 2:
            raise Exception("wrong number of fields")
        if row[0] in d:
            raise Exception("duplicate key")
        d[row[0]] = row[1].decode('utf8')
    return d


def load_rows_as_dict_of_dict(rows):
    d = {}
    for row in rows:
        if len(row) != 3:
            raise Exception("wrong number of fields")
        # values of 3 fields
        f1 = row[0]
        f2 = row[1]
        f3 = row[2].decode('utf8')
        if f1 in d:
            if f2 in d[f1]:
                raise Exception("duplicate key")
            else:
                d[f1][f2] = f3
        else:
            d[f1] = {f2: f3}
    return d


@lru_cache(maxsize=None)
def load_city_codes():
    rows = load_csv_file("city_codes.csv")
    commune_id_to_commune_name = load_rows_as_dict(rows)
    return commune_id_to_commune_name


@lru_cache(maxsize=None)
def load_contact_modes():
    rows = load_csv_file("contact_modes.csv")
    naf_prefix_to_rome_to_contact_mode = load_rows_as_dict_of_dict(rows)
    return naf_prefix_to_rome_to_contact_mode


@lru_cache(maxsize=None)
def load_ogr_labels():
    rows = load_csv_file("ogr_labels.csv")
    ogr_to_label = load_rows_as_dict(rows)
    return ogr_to_label


@lru_cache(maxsize=None)
def load_ogr_rome_mapping():
    rows = load_csv_file(OGR_ROME_FILE)

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
    rows = load_csv_file(ROME_FILE)
    rome_to_label = load_rows_as_dict(rows)
    return rome_to_label


@lru_cache(maxsize=None)
def load_naf_labels():
    rows = load_csv_file("naf_labels.csv")
    naf_to_label = load_rows_as_dict(rows)
    return naf_to_label


@lru_cache(maxsize=None)
def load_rome_naf_mapping():
    return load_csv_file(ROME_NAF_FILE, delimiter=',')



