# coding: utf8
import os
import itertools
import pandas as pd
from slugify import slugify

from labonneboite.conf import settings
from labonneboite.common import mapping as mapping_util
from labonneboite.common import geocoding
from labonneboite.common.search import fetch_companies

INPUT_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mailing_data/users_sample.csv')
OUTPUT_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mailing_data/users_sample_prepared.csv')

COMMUNE_COLUMN = 'Code INSEE commune'
ROME_1_COLUMN = 'ROME'
ROME_2_COLUMN = 'ROME 2'

COLUMNS_FOR_EACH_OFFICE = ['name', 'commune_id', 'commune_name', 'url']
OFFICES_PER_USER = 3
ADDITIONAL_COLUMNS = ['search_url', 'used_distance', 'used_rome_id'] + \
    [
        'office%s_%s' % (1+office_index, column_name)
            for office_index in range(OFFICES_PER_USER)
            for column_name in COLUMNS_FOR_EACH_OFFICE
    ]

# distances designed for Corsica
DISTANCE_ATTEMPTS = [10, 20, 30]

# tracking Google Analytics
GA_TRACKING_SEARCH = 'utm_medium=email&utm_source=mailing_corse_201710&utm_campaign=lien_recherche'
GA_TRACKING_DETAIL = 'utm_medium=email&utm_source=mailing_corse_201710&utm_campaign=lien_page_entreprise'


def get_results(commune_id, rome_1_id, rome_2_id):
    """
    Try to find enough offices matching this commune_id,
    for either of the two provided rome_ids,
    and within as small of a distance as possible.

    The result is a dictionary:
    - offices found
    - distance which was eventually used for the result
    - rome_id which was eventually used for the result
    """
    city = geocoding.get_city_by_commune_id(commune_id)

    if city is None:
        return {'offices': [], 'distance': settings.DISTANCE_FILTER_DEFAULT, 'rome_id': rome_1_id}

    latitude = city['coords']['lat']
    longitude = city['coords']['lon']

    offices = []

    # the only case where those stay None is if there is no result at all
    used_distance = None
    used_rome_id = None

    # about itertools.product see
    # https://stackoverflow.com/questions/16384109/iterate-over-all-combinations-of-values-in-multiple-lists-in-python
    for distance, rome_id in itertools.product(DISTANCE_ATTEMPTS, [rome_1_id, rome_2_id]):
        if mapping_util.rome_is_valid(rome_id):
            naf_code_list = mapping_util.map_romes_to_nafs([rome_id])
            offices, _, _ = fetch_companies(
                naf_codes=naf_code_list,
                rome_code=rome_id,
                latitude=latitude,
                longitude=longitude,
                distance=distance,
                from_number=1,
                to_number=OFFICES_PER_USER,
            )
            if len(offices) >= 1:
                used_rome_id = rome_id
                used_distance = distance
            if len(offices) >= OFFICES_PER_USER:
                break

    return {'offices': offices, 'distance': used_distance, 'rome_id': used_rome_id}


def get_search_url(commune_id, distance, rome_id):
    """
    Build search URL for given commune_id, distance and rome_id
    """
    if mapping_util.rome_is_valid(rome_id):
        rome_description = settings.ROME_DESCRIPTIONS[rome_id.upper()]
        slugified_rome_description = slugify(rome_description)
        city = geocoding.get_city_by_commune_id(commune_id)
        if city:
            # Here we hardcode the URL since this script typically runs in staging
            # for data confidentiality reasons and not in production.
            # However we need the resulting URLs to be pointing to production,
            # this is why we do not use `url_for`.
            search_url = 'https://labonneboite.pole-emploi.fr/entreprises/%s-%s/%s?d=%s&%s' % (
                city['slug'],
                city['zipcode'],
                slugified_rome_description,
                distance,
                GA_TRACKING_SEARCH,
            )
            return search_url
        
    return None


def compute_additional_data(commune_id, rome_1_id, rome_2_id):
    """
    Compute value of all additional CSV columns for a given commune_id and rome_id.
    """
    results = get_results(commune_id, rome_1_id, rome_2_id)
    offices = results['offices']
    distance = results['distance']
    rome_id = results['rome_id']

    search_url = get_search_url(commune_id, distance, rome_id)
    values = [search_url, distance, rome_id]

    for i in range(OFFICES_PER_USER):
        # about try except else
        # see https://stackoverflow.com/questions/16138232/is-it-a-good-practice-to-use-try-except-else-in-python
        try:
            office = offices[i]
        except IndexError:
            values += [''] * len(COLUMNS_FOR_EACH_OFFICE)
        else:
            office_url = 'https://labonneboite.pole-emploi.fr/%s/details?%s' % (
                office.siret,
                GA_TRACKING_DETAIL,
            )
            city = geocoding.get_city_by_commune_id(office.city_code)
            # names of these columns are in COLUMNS_FOR_EACH_OFFICE
            values += [office.company_name, office.city_code, city['slug'], office_url]


    return values


def prepare_mailing_data():
    """
	Enrich CSV user data in order to prepare mailing.
    """
    df = pd.read_table(INPUT_FILENAME, sep=',')

    # compute additional columns and add them to initial dataframe
    # inspired by
    # https://stackoverflow.com/questions/16236684/apply-pandas-function-to-column-to-create-multiple-new-columns
    # and https://stackoverflow.com/questions/13331698/how-to-apply-a-function-to-two-columns-of-pandas-dataframe
    temp = zip(*df[[COMMUNE_COLUMN, ROME_1_COLUMN, ROME_2_COLUMN]].apply(lambda x: compute_additional_data(*x), axis=1))
    for index, column in enumerate(ADDITIONAL_COLUMNS):
        df[column] = temp[index]

    # delete rows with empty or buggy results
    # df = df[condition] will remove from df all rows which do not match condition
    df = df[df.search_url.isnull() == False]  # FIXME ignore pylint warning
    df = df[df.office1_url.isnull() == False]  # FIXME ignore pylint warning

    # index=False avoids writing leading index column
    df.to_csv(OUTPUT_FILENAME, sep=',', index=False)


if __name__ == '__main__':
    prepare_mailing_data()
