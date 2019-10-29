import pandas as pd
import os

# get csv file from : https://datanova.legroupe.laposte.fr/explore/dataset/laposte_hexasmal/download/?format=csv&timezone=Europe/Berlin&use_labels_for_header=true
# To build a new file, we joined the old city codes files, and a new one found online
# We built it again because it was outdated, and many citycodes from new offices were not found anymore
# To make it work again, you have to prepare the two needed datasets : (new one, and old one), according to the good names
# A command in the Makefile can be found to start the script


def complete_citycodes(citycode):
    if len(citycode) == 4:
        citycode = "0%s" % citycode
    return citycode

# FIXME With Regex
def replace_saint_in_commune_name(commune_name, text='ST-'):
    index_position_st = commune_name.find(text)
    # If we find "ST" in the city name
    if index_position_st != -1:
        # If the char before "ST" is '-' or ST is the first word in the commune name, we can replace it with "SAINT"
        if commune_name[index_position_st-1] == '-' or index_position_st == 0:
            replacement_text = 'SAINT-' if text == 'ST-' else "SAINTE-"
            commune_name = commune_name.replace(text, replacement_text)

    return commune_name

# FIXME With Regex
def format_communename(row):
    commune_name = row['commune_name']
    commune_name = commune_name.strip()
    commune_name = commune_name.replace(' ', '-')
    commune_name = replace_saint_in_commune_name(commune_name, 'ST-')
    commune_name = replace_saint_in_commune_name(commune_name, 'STE-')

    if commune_name[0:2] == 'L-':
        commune_name = commune_name[2:]

    return commune_name


def clean_csv_city_codes():
    df_city_codes = pd.read_csv("common/data/laposte_hexasmal.csv",
                                sep=';',
                                header=0)

    df_city_codes.rename(columns={'Code_commune_INSEE': 'commune_id',
                                  'Nom_commune': 'commune_name'
                                  },
                         inplace=True)

    cols_of_interest = ['commune_id', 'commune_name']
    df_city_codes = df_city_codes[cols_of_interest]

    df_city_codes['commune_id'] = complete_citycodes(
        df_city_codes['commune_id'])

    df_city_codes['commune_name'] = df_city_codes.apply(
        lambda row: format_communename(row), axis=1)

    # Concatenation of old existing file and new one
    df_old_city_codes = pd.read_csv("common/data/old_city_codes.csv",
                                    sep='|',
                                    header=0)

    df_city_codes = pd.concat([df_city_codes, df_old_city_codes])

    df_city_codes = df_city_codes.drop_duplicates(
        subset=['commune_id', 'commune_name']
    )

    df_city_codes = df_city_codes.drop_duplicates('commune_id')

    df_city_codes = df_city_codes.sort_values('commune_id')

    df_city_codes.to_csv('common/data/city_codes.csv',
                         encoding='utf-8', sep='|', index=False)


if __name__ == '__main__':
    clean_csv_city_codes()
