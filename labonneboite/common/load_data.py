import os
import pickle
import csv
import pandas as pd
import math

from functools import lru_cache, reduce
from collections import defaultdict

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
    full_filename = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "data/%s" % filename)
    return func(full_filename)


def load_pickle_file(filename):
    def f(full_filename):
        return pickle.load(open(full_filename, "r"))
    return load_file(f, filename)

def load_pd_dataframe(filename, delimiter='', dtype=None):
    def f(full_filename):
        return pd.read_csv(open(full_filename, "r"), dtype=dtype)

    return load_file(f, filename)

def load_csv_file(filename, delimiter='|'):
    def f(full_filename):
        csv_file = open(full_filename, 'r')
        reader = csv.reader(csv_file, delimiter=delimiter)
        return reader

    reader = load_file(f, filename)
    rows = []
    len_previous_row = None

    for row in reader:
        if len_previous_row:
            # at least second line of CSV file
            if len(row) == 0:
                # skip empty rows
                continue
            elif len(row) != len_previous_row:
                raise IndexError(
                    "found row with abnormal number of fields : %s" % row)
            rows.append(row)
        else:
            # first line of CSV file: headers should be ignored
            pass

        len_previous_row = len(row)

    return rows


def load_rows_as_set(rows):
    for row in rows:
        if len(row) != 1:
            raise IndexError("wrong number of fields")
    return set([row[0] for row in rows])


def load_rows_as_dict(rows):
    d = {}
    for row in rows:
        if len(row) != 2:
            raise IndexError("wrong number of fields")
        if row[0] in d:
            raise ValueError("duplicate key")
        d[row[0]] = row[1]
    return d


def load_rows_as_dict_of_dict(rows):
    d = {}
    for row in rows:
        if len(row) != 3:
            raise IndexError("wrong number of fields")
        # values of 3 fields
        f1 = row[0]
        f2 = row[1]
        f3 = row[2]
        if f1 in d:
            if f2 in d[f1]:
                raise ValueError("duplicate key")
            else:
                d[f1][f2] = f3
        else:
            d[f1] = {f2: f3}
    return d


@lru_cache(maxsize=None)
def load_related_rome_areas():
    """
    Build a dict with department code (code insee) as keys and area code as values (bassins d'emploi).
    Used for PSE study in 2021.
    """
    rows = load_csv_file("lbb-pse_bassin-emploi_code-insee.csv", delimiter=';')
    return reduce(reduceRelateRomesAreas, rows, {})

def reduceRelateRomesAreas(aggr, row):
    [code_area, code_insee] = row
    aggr[code_insee] = code_area
    return aggr

@lru_cache(maxsize=None)
def load_related_rome():
    """
    Build a dict with area code (bassin d'emploi) as keys.
    The values are dict with rome code as keys and a list of related rome codes as values.
    Each related rome is a dict with `rome` and `score` properties.
    Used for PSE study.
    """
    rows = load_csv_file("lbb-pse_bassin-emploi_rome-connexe.csv", delimiter=';')
    return reduce(reduceRelateRomes, rows, {})

def reduceRelateRomes(aggr, row):
    [code_area, rome, rome_connexe, score] = row
    entry_code_area = aggr.get(code_area, {})
    entry_rome = entry_code_area.get(rome, [])
    entry_rome.append({'rome': rome_connexe, 'score': score})
    entry_code_area[rome] = entry_rome
    aggr[code_area] = entry_code_area
    return aggr

@lru_cache(maxsize=None)
def load_city_codes():
    rows = load_csv_file("city_codes.csv")
    commune_id_to_commune_name = load_rows_as_dict(rows)
    return commune_id_to_commune_name


@lru_cache(maxsize=None)
def load_contact_modes():
    """
    Use comma delimiter instead of pipe so that it is recognized by github
    and can easily be edited online by the intrapreneurs.
    """
    rows = load_csv_file("contact_modes.csv", delimiter=',')
    naf_prefix_to_rome_to_contact_mode = load_rows_as_dict_of_dict(rows)
    return naf_prefix_to_rome_to_contact_mode


@lru_cache(maxsize=None)
def load_ogr_labels():
    rows = load_csv_file("ogr_labels.csv")
    ogr_to_label = load_rows_as_dict(rows)
    return ogr_to_label


@lru_cache(maxsize=None)
def load_groupements_employeurs():
    rows = load_csv_file("groupements_employeurs.csv")
    sirets = load_rows_as_set(rows)
    return sirets


@lru_cache(maxsize=None)
def load_ogr_rome_mapping():
    rows = load_csv_file(OGR_ROME_FILE)

    OGR_COLUMN = 0
    ROME_COLUMN = 1
    ogr_to_rome = {}

    for row in rows:
        ogr = row[OGR_COLUMN]
        if ogr not in load_ogr_labels():
            raise ValueError("missing label for OGR %s" % ogr)

        rome = row[ROME_COLUMN]
        if rome not in load_rome_labels():
            raise ValueError("missing label for ROME %s" % rome)

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


@lru_cache(maxsize=None)
def load_metiers_tension():
    csv_metiers_tension = load_csv_file("metiers_tension.csv", ',')
    rome_to_tension = defaultdict(int)

    for row in csv_metiers_tension:
        tension_pct = row[2]
        rome_code = row[3]
        # FIXME : remove rows where tension is #N/A in the dataset, to remove this ugly check ?
        if tension_pct != '#N/A':
            tension_pct = float(tension_pct)
            if 0 <= tension_pct <= 100:
                # As a single ROME can have multiple tensions,
                # It has been decided to take the higher tension for a rome
                rome_to_tension[rome_code] = max(rome_to_tension[rome_code], tension_pct)
            else:
                raise ValueError
    return rome_to_tension

#Used for PSE study, it returns a list of SIRET that must not b be seen on LBB
@lru_cache(maxsize=None)
def load_siret_to_remove():
    rows = load_csv_file("untreated_BB.csv", ',')
    sirets_to_remove = load_rows_as_set(rows)

    return sirets_to_remove

#Used by importer job to extract etablissement
@lru_cache(maxsize=None)
def load_effectif_labels():
    '''
    Dataframe to load look like this.
        code      label
    0      0        0-0
    1      1        1-2
    2      2        3-5
    3      3        6-9
    4     11      10-19
    5     12      20-49
    6     21      50-99
    7     22    100-199
    8     31    200-249
    9     32    250-499
    10    41    500-999
    11    42  1000-1999
    12    51  2000-4999
    13    52  5000-9999
    14    53     10000+

    '''
    def create_column(row, which='start_effectif'):
        '''
        From the label, we want to create a start and end column to delimitate the interval
        We'll be able to use it to simply determine from a number of employees in an office, in which category the office belongs to  
        '''
        #we split on the label which is from type "10-19" OR 10000+
        splitted_label = row['label'].split('-')
        if len(splitted_label) == 1: #10000+
            value = math.inf if which == 'end_effectif' else 10000
        else:
            if which == 'start_effectif':
                value = int(splitted_label[0])
            else:
                value = int(splitted_label[1])

        return value

    df = load_pd_dataframe("helpers/effectif_labels.csv", ',', dtype={'code':str})
    df['start_effectif'] = df.apply(lambda row: create_column(row,'start_effectif'), axis=1)
    df['end_effectif'] = df.apply(lambda row: create_column(row,'end_effectif'), axis=1)

    return df


OGR_ROME_CODES = load_ogr_rome_mapping()
ROME_CODES = list(OGR_ROME_CODES.values())

