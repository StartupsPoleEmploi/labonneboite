import pandas as pd
import ipdb
import os

# get csv file from : https://datanova.legroupe.laposte.fr/explore/dataset/laposte_hexasmal/download/?format=csv&timezone=Europe/Berlin&use_labels_for_header=true

df_city_codes = pd.read_csv("../../common/data/laposte_hexasmal.csv",
                            sep=';',
                            header=0)

df_city_codes.rename(columns={'Code_commune_INSEE': 'commune_id',
                              'Nom_commune': 'commune_name'
                              },
                     inplace=True)

cols_of_interest = ['commune_id', 'commune_name']
df_city_codes = df_city_codes[cols_of_interest]


def complete_citycodes(citycode):
    if len(citycode) == 4:
        citycode = "0%s" % citycode
    return citycode

df_city_codes['commune_id'] = complete_citycodes(df_city_codes['commune_id'])

def format_communename(row):
    commune_name = row['commune_name']
    commune_name = commune_name.replace(' ', '-')
    commune_name = commune_name.replace('ST', 'SAINT')
    if commune_name[0:2] == 'L-':
        commune_name = commune_name[2:]

    return commune_name

df_city_codes['commune_name'] = df_city_codes.apply(
    lambda row: format_communename(row), axis=1)

#Concatenation of old existing file and new one
df_old_city_codes = pd.read_csv("../../common/data/old_city_codes.csv",
                            sep='|',
                            header=0)

df_city_codes = pd.concat([df_city_codes,df_old_city_codes])

df_city_codes = df_city_codes.drop_duplicates(
    subset=['commune_id', 'commune_name']
)

df_city_codes = df_city_codes.sort_values('commune_id')

df_city_codes.to_csv('../../common/data/city_codes.csv', encoding='utf-8', sep='|', index=False)