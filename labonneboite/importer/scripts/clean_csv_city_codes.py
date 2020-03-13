import os
import re

import pandas as pd


# get csv file from : https://datanova.legroupe.laposte.fr/explore/dataset/laposte_hexasmal/download/?format=csv&timezone=Europe/Berlin&use_labels_for_header=true
# To build a new file, we joined the old city codes files, and a new one found online
# We built it again because it was outdated, and many citycodes from new offices were not found anymore
# To make it work again, you have to prepare the two needed datasets : (new one, and old one), according to the good names
# A command in the Makefile can be found to start the script


class WrongFormatCityCodeException(Exception):
    pass


def complete_citycodes(row):
    citycode = row["commune_id"]
    if len(citycode) <= 3 or len(citycode) >= 6:
        raise WrongFormatCityCodeException()
    elif len(citycode) == 4:
        citycode = "0%s" % citycode

    return citycode


def replace_saint_in_commune_name(commune_name):
    commune_name = re.sub("-ST-", "-SAINT-", commune_name)
    commune_name = re.sub("^ST-", "SAINT-", commune_name)
    commune_name = re.sub("-STE-", "-SAINTE-", commune_name)
    commune_name = re.sub("^STE-", "SAINTE-", commune_name)
    return commune_name


def format_communename(row):
    commune_name = row["commune_name"]
    commune_name = commune_name.strip()
    commune_name = commune_name.replace(" ", "-")
    commune_name = replace_saint_in_commune_name(commune_name)

    if commune_name[0:2] == "L-":
        commune_name = commune_name[2:]

    return commune_name


def clean_csv_city_codes():
    df_city_codes = pd.read_csv("common/data/laposte_hexasmal.csv", sep=";", header=0)

    df_city_codes.rename(columns={"Code_commune_INSEE": "commune_id", "Nom_commune": "commune_name"}, inplace=True)

    cols_of_interest = ["commune_id", "commune_name"]
    df_city_codes = df_city_codes[cols_of_interest]

    df_city_codes["commune_id"] = df_city_codes.apply(lambda row: complete_citycodes(row), axis=1)

    df_city_codes["commune_name"] = df_city_codes.apply(lambda row: format_communename(row), axis=1)

    # Concatenation of old existing file and new one
    df_old_city_codes = pd.read_csv("common/data/old_city_codes.csv", sep="|", header=0)

    df_city_codes = pd.concat([df_city_codes, df_old_city_codes])

    df_city_codes = df_city_codes.drop_duplicates(subset=["commune_id", "commune_name"])

    df_city_codes = df_city_codes.drop_duplicates("commune_id")

    df_city_codes = df_city_codes.sort_values("commune_id")

    df_city_codes.to_csv("common/data/city_codes.csv", encoding="utf-8", sep="|", index=False)


if __name__ == "__main__":
    clean_csv_city_codes()
