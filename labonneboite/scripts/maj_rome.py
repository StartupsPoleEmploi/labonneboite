import pandas as pd

# This script has been written to :
# - Update Rome labels
# - Add and update Ogr labels
# - Add more mapping rome OGR
# - Update rome labels in mapping rome naf
#
# We use the data updated by Pole Emploi :
# https://www.pole-emploi.org/opendata/repertoire-operationnel-des-meti.html?type=article
#
# You can download the main dataset (common/data/arbo_rome_ogr_2020.csv) on this link :
# https://www.pole-emploi.org/files/live/sites/peorg/files/documents/Statistiques-et-analyses/Open-data/ROME/ROME_ArboPrincipale.xlsx


def concat_rome_columns(row):
    return row['Rome1'] + row['Rome2'] + row['Rome3']


def load_main_rome_arbo():
    file_name = "common/data/arbo_rome_ogr_202107.csv"
    df_main = pd.read_csv(file_name, delimiter=';')
    df_main['Rome'] = df_main.apply(lambda row: concat_rome_columns(row), axis=1)

    return df_main


def update_rome_labels(df_main):
    df_rome_labels = df_main[df_main.OGR == ' ']
    df_rome_labels = df_rome_labels[df_rome_labels.Rome.str.len() == 5]

    # Analysis note :
    # There are the same number of rome in both files, we can safely update the files
    df_rome_labels = df_rome_labels[['Rome', 'Intitule']]

    df_rome_labels.rename(columns={
        'Rome': 'rome_id',
        'Intitule': 'rome_label'
    }, inplace=True)

    df_rome_labels.to_csv('common/data/rome_labels.csv', sep='|', index=False)

    return df_rome_labels


def update_ogr_labels(df_main):
    df_ogr_labels = df_main[df_main.OGR != ' ']

    # Analysis note :
    # We have arround 100 ogr codes more than the previous dataset, it's ok to update !
    df_ogr_labels = df_ogr_labels[['OGR', 'Intitule']]

    df_ogr_labels.rename(columns={
        'OGR': 'ogr_id',
        'Intitule': 'ogr_label'
    }, inplace=True)

    df_ogr_labels = df_ogr_labels.sort_values(by=['ogr_id'])

    df_ogr_labels.to_csv('common/data/ogr_labels.csv', sep='|', index=False)

    return df_ogr_labels


def update_ogr_rome_mapping(df_main):
    df_ogr_rome_mapping = df_main[df_main.OGR != ' ']

    # Analysis note :
    # We have arround 100 ogr codes more than the previous dataset, it's ok to update !
    df_ogr_rome_mapping = df_ogr_rome_mapping[['OGR', 'Rome']]

    df_ogr_rome_mapping.rename(columns={
        'OGR': 'ogr_id',
        'Rome': 'rome_id'
    }, inplace=True)

    df_ogr_rome_mapping = df_ogr_rome_mapping.sort_values(by=['ogr_id'])

    df_ogr_rome_mapping.to_csv('common/data/ogr_rome_mapping.csv', sep='|', index=False)

    return df_ogr_rome_mapping


def update_rome_naf_mapping(df_rome_labels):
    df_rome_naf_mapping_old = pd.read_csv("common/data/rome_naf_mapping_2021.csv", delimiter=',')
    df_rome_naf_mapping = df_rome_naf_mapping_old.merge(df_rome_labels, on=('rome_id'), suffixes=('_old', '_new'))
    df_rome_naf_mapping = df_rome_naf_mapping[["rome_id", "rome_label_new", "naf_id", "naf_label", "hirings"]]
    df_rome_naf_mapping.rename(columns={'rome_label_new': 'rome_label'}, inplace=True)
    df_rome_naf_mapping.to_csv('common/data/rome_naf_mapping.csv', sep=',', index=False)

    return df_rome_naf_mapping


if __name__ == '__main__':
    df_main_new = load_main_rome_arbo()
    df_rome_labels_new = update_rome_labels(df_main_new)
    df_ogr_labels_new = update_ogr_labels(df_main_new)
    df_ogr_rome_mapping_new = update_ogr_rome_mapping(df_main_new)
    df_rome_naf_mapping_new = update_rome_naf_mapping(df_rome_labels_new)
