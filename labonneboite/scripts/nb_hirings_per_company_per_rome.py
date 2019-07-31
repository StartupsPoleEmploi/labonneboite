import pandas as pd
import datetime

from labonneboite.importer import util as import_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common import mapping as mapping_util
from labonneboite.importer import settings as importer_settings

def get_total_hirings_per_company():
    engine = import_util.create_sqlalchemy_engine()

    query = "select \
                siret, \
                codenaf, \
                codepostal, \
                codecommune, \
                trancheeffectif, \
                greatest(0, floor(score_regr)) as total_hirings \
             from \
                etablissements_backoffice;"

    df_total_hirings = pd.read_sql_query(query, engine)

    engine.close()

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

def get_score_from_hirings(df_total_hirings):

    def get_score(row):
        return scoring_util._get_score_from_hirings(row['total_hirings'])

    df_total_hirings['total_score'] = df_total_hirings.apply(
        lambda row: get_score(row), axis=1)

    # FIXME : oneliner which does the same thing than above, but does not work hehehehe
    # df_total_hirings['score bis'] = df_total_hirings.apply(lambda row: scoring_util._get_score_from_hirings(row.total_hirings))

    def get_romes(row):
        try:
            romes = mapping_util.get_romes_for_naf(row['codenaf'])
            # FIXME : wow it's ugly, will be fixed when we'll find another way to split the dataframe
            return str(romes).replace(' ', '').replace('\'', '')[1:-1]
        except KeyError:
            # unfortunately some NAF codes have no matching ROME at all
            return ''

    df_total_hirings['rome'] = df_total_hirings.apply(
        lambda row: get_romes(row), axis=1)

    # FIXME : Will create a huuuuuuge dataframe, not a nice way to do
    df_total_hirings = splitDataFrameList(df_total_hirings, 'rome', ',')

    def get_true_score(row):
        return scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
            score=row['total_score'],
            rome_code=row['rome'],
            naf_code=row['codenaf'])

    df_total_hirings['true_score'] = df_total_hirings.apply(
        lambda row: get_true_score(row), axis=1)

    # TODO : Filter on low scores, or the dataset will really be huge
    # df_total_hirings = df_total_hirings[df_total_hirings['true_score'] >= 20]
    # TODO : Maybe need to rajouter une colonne seuil, construite, comme dans le daily create index, en prenant en compte les métiers en tension

    def get_true_hirings(row):
        return scoring_util.get_hirings_from_score(row['true_score'])

    df_total_hirings['nb_recrutements_predits'] = df_total_hirings.apply(
        lambda row: get_true_hirings(row), axis=1)

    cols_of_interest = ['siret',
                        'codenaf',
                        'rome',
                        'codepostal',
                        'codecommune',
                        'trancheeffectif',
                        'nb_recrutements_predits']

    df_total_hirings = df_total_hirings[cols_of_interest]

    return df_total_hirings


def run_main():
    df_total_hirings = get_total_hirings_per_company()
    df_total_hirings = get_score_from_hirings(df_total_hirings)
    path = '{}/prediction_per_company_per_rome{}.csv'.format(
        importer_settings.INPUT_SOURCE_FOLDER, str(datetime.date.today()))
    print(path)
    df_total_hirings.to_csv(path)

if __name__ == '__main__':
    run_main()
