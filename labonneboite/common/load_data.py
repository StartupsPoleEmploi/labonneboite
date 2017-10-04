import os
import pickle
import csv

from labonneboite.conf import settings
from backports.functools_lru_cache import lru_cache


def load_file(fun, filename):
    full_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/%s" % filename)
    return fun(full_filename)


def load_pickle_file(filename):
    def f(full_filename):
        return pickle.load(open(full_filename, "r"))
    return load_file(f, filename)


def load_csv_file(filename):
    def f(full_filename):
        csv_file = open(full_filename, 'rb')
        reader = csv.reader(csv_file, delimiter=',')
        return reader
    return load_file(f, filename)


@lru_cache(maxsize=None)
def load_city_codes():
    return load_pickle_file("city_codes_v2.pickle")


@lru_cache(maxsize=None)
def load_contact_modes():
    return load_pickle_file("contact_modes.pickle")


@lru_cache(maxsize=None)
def load_ogr_labels():
    return load_pickle_file("ogr_labels.pickle")


@lru_cache(maxsize=None)
def load_ogr_rome_codes():
    reader = load_csv_file("ogr_rome_mapping.csv")

    OGR_COLUMN = 0
    ROME_COLUMN = 1
    ogr_to_rome = {}

    for column in reader:
        ogr_to_rome[column[OGR_COLUMN]] = column[ROME_COLUMN]

    return ogr_to_rome


@lru_cache(maxsize=None)
def load_manual_rome_naf_file():
    return load_csv_file("rome_naf_mapping.csv")



