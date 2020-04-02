import datetime
import pandas as pd

from labonneboite.importer import util as import_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common import mapping as mapping_util
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.jobs.common import logger
from labonneboite.common.env import get_current_env, ENV_DEVELOPMENT


def get_total_hirings_per_office():
    engine = import_util.create_sqlalchemy_engine()

    query = "select\
                siret,\
                raisonsociale,\
                enseigne,\
                email,\
                tel,\
                website,\
                codenaf,\
                codepostal,\
                codecommune,\
                trancheeffectif,\
                greatest(0, floor(score_regr)) as total_hirings\
             from \
                etablissements_backoffice"

    # To make it work in local dev, we have to take all the offices that have score > 0
    if get_current_env() != ENV_DEVELOPMENT:
        query += " where greatest(0, floor(score_regr)) > 0;"

    df_total_hirings = pd.read_sql_query(query, engine)

    engine.close()
    logger.info("Datas selected from etablissements_backoffice")
    print(df_total_hirings)
    return df_total_hirings

# function found on gist.github : https://gist.github.com/jlln/338b4b0b55bd6984f883


def splitDataFrameList(df, target_column, separator):
    ''' df = dataframe to split,
    target_column = the column containing the values to split
    separator = the symbol used to perform the split
    returns: a dataframe with each entry for the target column separated, with each element moved into a new row.
    The values in the other columns are duplicated across the newly divided rows.
    '''
    def splitListToRows(row, row_accumulator, target_column, separator):
        split_row = row[target_column].split(separator)
        for s in split_row:
            new_row = row.to_dict()
            new_row[target_column] = s
            row_accumulator.append(new_row)
    new_rows = []
    df.apply(splitListToRows, axis=1, args=(
        new_rows, target_column, separator))
    new_df = pd.DataFrame(new_rows)
    return new_df


def get_score(row):
    return scoring_util._get_score_from_hirings(row['total_hirings'])


def get_romes(row):
    try:
        romes = mapping_util.get_romes_for_naf(row['codenaf'])
        # FIXME : wow it's ugly, will be fixed when we'll find another way to split the dataframe
        return str(romes).replace(' ', '').replace('\'', '')[1:-1]
    except KeyError:
        # unfortunately some NAF codes have no matching ROME at all
        return ''


def get_true_score(row):
    return scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
        score=row['total_score'],
        rome_code=row['rome'],
        naf_code=row['codenaf'])


def get_true_hirings(row):
    return scoring_util.get_hirings_from_score(row['score'])


def is_a_bonne_boite(row):
    return row['score'] >= row['seuil']


def get_offices_are_bonne_boite(df_total_hirings):

    df_total_hirings['total_score'] = df_total_hirings.apply(lambda row: get_score(row), axis=1)
    logger.info("Total score just has been computed for each row")

    df_total_hirings['rome'] = df_total_hirings.apply(lambda row: get_romes(row), axis=1)
    logger.info("We got all romes related to each NAF and stored a list in a cell")

    df_total_hirings = splitDataFrameList(df_total_hirings, 'rome', ',')
    logger.info("We split each row from 1 naf multiple romes --> 1 naf 1 rome")

    df_total_hirings['score'] = df_total_hirings.apply(lambda row: get_true_score(row), axis=1)
    logger.info("We compute the true score for each row")

    df_total_hirings['nb_recrutements_predits'] = df_total_hirings.apply(lambda row: get_true_hirings(row), axis=1)
    logger.info("We compute the true hirings for each row")

    cols_of_interest = ['siret',
                        'raisonsociale',
                        'enseigne',
                        'email',
                        'tel',
                        'website',
                        'codenaf',
                        'rome',
                        'codepostal',
                        'codecommune',
                        'trancheeffectif',
                        'nb_recrutements_predits',
                        'score']

    df_total_hirings = df_total_hirings[cols_of_interest]

    df_total_hirings['seuil'] = df_total_hirings['rome'].apply(lambda x: scoring_util.get_score_minimum_for_rome(x))
    logger.info("We compute the threshold, related to the score column. If a score is >= to this threshold, it's considered as a office")

    df_total_hirings['is a bonne boite ?'] = df_total_hirings.apply(lambda row: is_a_bonne_boite(row), axis=1)
    logger.info("We added a column to tell if its a bonne boite or no")

    return df_total_hirings


def get_nb_bonne_boite_per_rome(df):
    return df.groupby(['rome'])['is a bonne boite ?'].sum()


def run_main():
    # Get the file for PSE that compute the nb of hirings per rome per office
    df_total_hirings = get_total_hirings_per_office()
    df_total_hirings = get_offices_are_bonne_boite(df_total_hirings)
    date_today = str(datetime.date.today())
    path = f'{importer_settings.INPUT_SOURCE_FOLDER}/nb_hirings_per_office-{date_today}.csv'
    df_total_hirings.to_csv(path)
    print(f"File has been saved in {path}")

    # Get the file for PSE that compute the nb of hirings per rome per office
    df_nb_bonne_boite_per_rome = get_nb_bonne_boite_per_rome(df_total_hirings)
    path = f'{importer_settings.INPUT_SOURCE_FOLDER}/nb_bonne_boite_per_rome-{date_today}.csv'
    df_nb_bonne_boite_per_rome.to_csv(path, header=['nb_bonnes_boites'])
    print(f"File has been saved in {path}")


if __name__ == '__main__':
    run_main()
