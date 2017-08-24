import os
import pickle
import csv

from labonneboite.conf import settings

CACHE = {}


def load_file(fun, filename):
    if filename in CACHE:
        return CACHE[filename]
    else:
        full_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/%s" % filename)
        CACHE[filename] = fun(full_filename)
        return CACHE[filename]


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


def load_city_codes():
    return load_pickle_file("city_codes_v2.pickle")


def load_contact_modes():
    return load_pickle_file("contact_modes.pickle")


def load_ogr_labels():
    return load_pickle_file("ogr_labels.pickle")


def load_ogr_rome_codes():
    return load_pickle_file("ogr_rome_codes.pickle")


def load_manual_rome_naf_file():
    return load_csv_file(settings.MANUAL_ROME_NAF_FILENAME)
