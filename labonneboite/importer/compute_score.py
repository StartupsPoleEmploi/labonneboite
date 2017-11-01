# coding: utf-8
"""Machine learning module.

The outside world uses the "run" function which will predict how many hirings a company will make in the next 6 months,
and we use a regression model to do so. The predicted number of hirings is then transformed into a "score" value
between 0 and 100 for each office ("etablissement").

We train a machine learning algorithm on companies and employment data to create this score.

We use the scikit-learn library : more info http://scikit-learn.org/stable/documentation.html
"""
import sys

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from operator import getitem

import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.pool import NullPool
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.models.computing import DpaeStatistics
from labonneboite.common import scoring as scoring_util
from labonneboite.common.database import get_db_string
import pickle
import os
from urlparse import urlparse
import validators

import logging
from debug import listen

logger = logging.getLogger('main')
listen()

# Output additional debug info about these sirets
# To disable, set to an empty list []
# Sirets must be string, not int
DEBUG_SIRETS = ["19240023200018", "33530956300047", "26760168000015"]
# DEBUG_SIRETS = []

# disable unnecessary SettingWithCopyWarning
# see http://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
pd.options.mode.chained_assignment = None  # default='warn'


class NotEnoughDataException(Exception):
    pass


def raise_with_message(msg):
    logger.info("WARNING exception: %s", msg)
    raise Exception(msg)


def debug_df(df, description="no description"):
    if len(DEBUG_SIRETS) >= 1:
        logger.debug("dataframe debug info [%s] about sirets %s", 
                     description, DEBUG_SIRETS)
        columns = list(df.columns)
        logger.debug("dataframe has %s rows and columns = %s", len(df), columns)
        if "siret" in columns:
            tmp_df = df[df.siret.isin(DEBUG_SIRETS)]
            logger.debug("dataframe content :\n %s", tmp_df)
        else:
            logger.debug("dataframe does not have a siret colum")
            logger.debug("columns : %s", columns)


def discarded_check(departement):
    # weird data distribution for these departements, discard safey
    return int(departement) in [20, ]


def check_coefficient_of_variation(departement, coefficient_of_variation):
    logger.info("checking mean_between_existing_and_new_score: %s", coefficient_of_variation)
    if not discarded_check(departement):
        if not coefficient_of_variation < importer_settings.SCORE_COEFFICIENT_OF_VARIATION_MAX:
            raise_with_message("coefficient_of_variation too high: %s > %s" % (
                coefficient_of_variation, importer_settings.SCORE_COEFFICIENT_OF_VARIATION_MAX
            ))


def check_mean_between_existing_and_new_score(departement, df):
    mean = np.nan_to_num(df[["diff_score"]].mean())[0]
    logger.info("checking mean_between_existing_and_new_score: %s", mean)
    if not discarded_check(departement):
        if not np.nan_to_num(df[["diff_score"]].mean())[0] < importer_settings.SCORE_COMPUTING_MAX_DIFF_MEAN:
            raise "np.nan_to_num(df[[\"diff_score\"]].mean())[0] too high"


def check_highly_scored_companies_evolution(departement, high_existing_scores, high_new_scores):
    evolution = 100 * abs(high_new_scores - high_existing_scores) / high_existing_scores
    logger.info("highly_scored_companies_evolution: %s", evolution)
    if not discarded_check(departement):
        if not evolution < importer_settings.HIGH_SCORE_COMPANIES_DIFF_MAX:
            raise_with_message("evolution too high: %s > %s" % (evolution, importer_settings.HIGH_SCORE_COMPANIES_DIFF_MAX))


def check_number_highly_scored_companies(departement, high_new_scores):
    if not discarded_check(departement):
        if not high_new_scores > importer_settings.HIGH_SCORE_COMPANIES_COUNT_MIN:
            error_msg = "high_new_scores too low: %s < %s" % (high_new_scores, importer_settings.HIGH_SCORE_COMPANIES_COUNT_MIN)
            raise Exception(error_msg)


def normalize_website_url(url):
    """
    website URLs are raw data entered by human, with lots of mistakes,
    so it has to be automatically cleaned up and normalized
    """
    if (not url) or ('@' in url) or ('.' not in url) or (len(url) <= 3):
        return None

    url = url.replace('"', '').strip()

    # add missing http prefix if needed
    if not urlparse(url).scheme:
        url = "http://" + url

    # normalization
    try:
        url = urlparse(url).geturl()
    except ValueError:
        return None

    # ensure website URL is correct (and is not an email address for example!)
    try:
        validators.url(url)
    except validators.ValidationFailure:
        return None

    return url


# def merge_and_normalize_websites(w1, w2):
def merge_and_normalize_websites(websites):
    w1, w2 = websites
    w1 = normalize_website_url(w1)
    w2 = normalize_website_url(w2)
    if w1:
        return w1
    elif w2:
        return w2
    else:
        return ""


def load_df(engine, etablissement_table, dpae_table, departement, most_recent_data_date):
    logger.debug("reading data with most recent data date %s...", most_recent_data_date)
    if departement:
        logger.debug("filtering by departement (%s)...", departement)
        # keep only contract_type = 2 (CDI) and contract_type = 1 (CDD which last at least one month)
        df = pd.read_sql_query("""
            select siret, hiring_date, contract_type, contract_duration from %s where departement = %s
            and (contract_type = 2 or (contract_type = 1 and contract_duration > 31))
            """ % (dpae_table, departement), engine)
        debug_df(df, "after loading from dpae table")
        if df.empty:
            logger.warning("no dpae data for departement %s", departement)
            return None
        logger.debug("reading data from etablissements (%s)", departement)
        df_etab = pd.read_sql_query("""
            select * from %s where departement = %s and siret != ''
            """ % (etablissement_table, departement), engine)
        debug_df(df_etab, "after loading from etablissements_prod table")
        if "website1" not in list(df_etab.columns):
            raise Exception("missing website1 column")

        # tricky dataframe operation: merge two columns into one using an element wise function
        # http://stackoverflow.com/questions/13331698/how-to-apply-a-function-to-two-columns-of-pandas-dataframe
        df_etab["website"] = df_etab[['website1', 'website2']].apply(merge_and_normalize_websites, axis=1)
        debug_df(df_etab, "after processing website")
        del df_etab['website1']
        del df_etab['website2']
        debug_df(df_etab, "after removing website1 and website2")
        if "website" not in list(df_etab.columns):
            raise Exception("missing website column")

        if df_etab.empty:
            logger.warning("dataframe empty for departement %s", departement)
            return None
    else:
        # FIXME cleanup - or reuse soon as we will compute all departements with a single model!?
        raise Exception("this code is never supposed to run")
        logger.debug("selecting data from france, gonna be slow...")
        df = pd.read_sql(dpae_table, engine)
        logger.debug("reading data from etablissements")
        df_etab = pd.read_sql(etablissement_table, engine)
    logger.debug("loading data (%s) OK (%i etablissements)!", departement, len(df_etab))

    debug_df(df, "before various filterings")
    df = df[df.hiring_date >= importer_settings.FIRST_DAY_DPAE]
    debug_df(df, "after filtering hiring_date >= importer_settings.FIRST_DAY_DPAE")
    df = df[df.hiring_date <= most_recent_data_date]
    debug_df(df, "after filtering hiring_date <= most_recent_data_date")

    df["hiring_date_month"] = pd.DatetimeIndex(df["hiring_date"]).month
    df["hiring_date_year"] = pd.DatetimeIndex(df["hiring_date"]).year

    df2 = df.groupby(["siret", "hiring_date_year", "hiring_date_month"]).count().reset_index()
    debug_df(df2, "after group by")
    logger.debug("pivoting table dpae (%s)...", departement)
    df3 = pd.pivot_table(df2, values="hiring_date", index="siret", columns=["hiring_date_year", "hiring_date_month"])
    debug_df(df3, "after pivot")
    logger.debug("pivoting table (%s) ok!", departement)
    df3["siret"] = df3.index
    df3 = df3.fillna(0)

    df3.columns = [''.join(str(col).strip()) for col in df3.columns.values]
    df3['siret'] = df3[u"('siret', '')"]
    debug_df(df3, "after transform")

    logger.debug("merging dpae with etablissements (%s)...", departement)
    # inner join to keep only etabs which have at least one dpae
    df_final = pd.merge(df3, df_etab, on='siret', how="inner")
    debug_df(df_final, "after merge")
    logger.debug("merging done with %s offices(%s)!", len(df_final), departement)
    if "website" not in list(df_final.columns):
        raise Exception("missing website column")

    df_final = df_final.fillna(0)

    # Add effectif from trancheeffectif
    def tranche_to_effectif(tranche):
        map_tranche_to_effectif = {
            '00': 0,
            '01': 1,
            '02': 3,
            '03': 6,
            '11': 10,
            '12': 20,
            '21': 50,
            '22': 100,
            '31': 200,
            '32': 250,
            '41': 500,
            '42': 1000,
            '51': 2000,
            '52': 5000,
            '53': 10000
        }
        if tranche not in map_tranche_to_effectif.keys():
            return 1
        return map_tranche_to_effectif[tranche]

    logger.debug("adding effectif (%s)...", departement)
    df_final['effectif'] = df_final['trancheeffectif'].map(tranche_to_effectif)
    logger.debug("effectif done (%s)!", departement)

    return df_final, df3


def compute_reference_date(most_recent_data_date):
    # let's decide what is the reference date
    # that is, the date from which we will make predictions (for the next 6 months)
    # if the last data we have is just for the beginning of the month,
    # we will make predictions from the first day of the month
    # otherwise, if we have data for the full month
    # we'll start our predictions from the first day of following month
    if most_recent_data_date.day > 25:
        if most_recent_data_date.month == 12:
            month_reference = 1
            year_reference = most_recent_data_date.year + 1
        else:
            month_reference = most_recent_data_date.month + 1
            year_reference = most_recent_data_date.year
    else:
        month_reference = most_recent_data_date.month
        year_reference = most_recent_data_date.year
    reference_date = date(year_reference, month_reference, 1)

    logger.info("reference date %s", reference_date)
    return reference_date


def has_hired_semester(semester):
    def f(office):
        return office[semester] > 0
    return f


def total_hired_semester(semester):
    def f(office):
        return office[semester]
    return f


def create_feature_vector(df, semester_lag, debug_msg="Unnamed", get_feature_names=False):
    temporal_features = []
    for i in reversed(range(1, 5)):
        index = semester_lag + 1 + i
        temporal_features.append('semester-%i' % index)
    features = list(temporal_features)
    features.append('effectif')

    df_features_only = df[features]
    X = df_features_only.values

    df_for_debug = df[["siret"] + features]
    debug_df(df_for_debug, debug_msg)

    if get_feature_names:
        return X, features
    else:
        return X


def add_features(df_final, departement, reference_date, feature_semester_count, semester_lag, get_feature_names=False):
    def hiring_count_semester(office, minus):
        start_date = reference_date + relativedelta(months=-6 * minus - 1)
        columns = []
        for i in range(1, feature_semester_count):
            current_date = start_date + relativedelta(months=+i)
            columns.append(u'(%s, %s)' % (current_date.year, current_date.month))
        dpae_semester = []
        for column in columns:
            try:
                each_month = getitem(office, column)
            except KeyError:
                each_month = 0
            dpae_semester.append(each_month)
        return sum(dpae_semester)

    logger.debug("computing dpae aggregates (%s)...", departement)

    semester_count_columns = []
    for i in range(1, feature_semester_count + 1):
        column = 'semester-%s' % i
        df_final[column] = df_final.apply(lambda office: hiring_count_semester(office, i), axis=1)
        semester_count_columns.append(column)
    logger.debug("finished calculating temporal features (%s)!", departement)

    hiring_count_per_semester_sum = df_final[semester_count_columns].sum(axis=0)
    coefficient_of_variation = hiring_count_per_semester_sum.std() / hiring_count_per_semester_sum.mean()
    logger.debug('hiring_count_per_semester_sum %s', hiring_count_per_semester_sum)
    logger.debug('coefficient of variation of DPAE count per semester %s', coefficient_of_variation)

    check_coefficient_of_variation(departement, coefficient_of_variation)

    X, X_feature_names = create_feature_vector(df_final,
                                               semester_lag,
                                               debug_msg="add_features (X_train)",
                                               get_feature_names=True)

    semester = 'semester-%i' % (semester_lag + 1)
    logger.debug("outcome: has hired in %s", semester)
    y = df_final.apply(has_hired_semester(semester), axis=1)
    y_regr = df_final.apply(total_hired_semester(semester), axis=1)
    if get_feature_names:
        return df_final, X, y, y_regr, X_feature_names
    else:
        return df_final, X, y, y_regr


def train(df_final, departement, reference_date, semester_lag, feature_semester_count=7):

    # 1) --- modeling the problem as a binary classification
    # from sklearn.ensemble import RandomForestClassifier
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import precision_recall_fscore_support
    # from sklearn.metrics import precision_score, classification_report, recall_score
    # clf = LogisticRegression()
    # clf = RandomForestClassifier()
    clf = GradientBoostingClassifier()

    # 2) --- modeling the problem as a regression
    from sklearn import linear_model
    from sklearn.metrics import mean_squared_error
    regr = linear_model.LinearRegression()

    df_final, X_train, y_train_bin, y_train_regr, X_train_feature_names = add_features(
        df_final,
        departement,
        reference_date,
        feature_semester_count,
        semester_lag,
        get_feature_names=True)
    debug_df(df_final, "df_final after add_features")
    logger.debug("X_train_feature_names: %s", X_train_feature_names)

    logger.debug("%s offices (%s)", len(df_final), departement)

    if len(df_final) < 50:
        # problems happen if we don't have enough offices to train on...
        # throw an exception to show we don't have enough data for this departement
        raise NotEnoughDataException("only %s offices !" % len(df_final))
    logger.debug("fitting the model on X_train (%s)...", departement)
    clf.fit(X_train, y_train_bin)
    regr.fit(X_train, y_train_regr)
    logger.debug("regression_coefficients (fitting done on X_train) : %s", regr.coef_)
    logger.debug("fitting done (%s)!", departement)

    y_train_bin_pred = clf.predict(X_train)
    y_train_regr_pred = regr.predict(X_train)

    X_test, X_test_feature_names = create_feature_vector(df_final, 0, debug_msg="X_test", get_feature_names=True)
    logger.debug("X_test_feature_names: %s", X_test_feature_names)
    y_test_bin = df_final.apply(has_hired_semester('semester-1'), axis=1)
    y_test_bin_pred = clf.predict(X_test)
    y_test_regr = df_final.apply(total_hired_semester('semester-1'), axis=1)
    y_test_regr_pred = regr.predict(X_test)

    X_live, X_live_feature_names = create_feature_vector(df_final, -2 + semester_lag, debug_msg="X_live", get_feature_names=True)
    logger.debug("X_live_feature_names: %s", X_live_feature_names)

    # 1) --- binary classification metrics
    precision_train, recall_train, _, _ = precision_recall_fscore_support(y_train_bin, y_train_bin_pred)
    precision, recall, fscore, support = precision_recall_fscore_support(y_test_bin, y_test_bin_pred)
    # 2) --- regression metrics
    rmse_train = mean_squared_error(y_train_regr, y_train_regr_pred)
    rmse_test = mean_squared_error(y_test_regr, y_test_regr_pred)

    pickle_data = {
        "departement": departement,
        "X_train_feature_names": X_train_feature_names,
        "X_test_feature_names": X_test_feature_names,
        "X_live_feature_names": X_live_feature_names,
        "classifier": clf,
        "classifier_scores": {
            "precision": precision,
            "precision_train": precision_train,
            "recall": recall,
            "recall_train": recall_train,
            "fscore": fscore,
            "support": support
        },
        "regression": regr,
        "regression_coefficients": regr.coef_,
        "regression_scores": {
            "rmse_train": rmse_train,
            "rmse_test": rmse_test,
        }
    }

    current_time = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    pickle_folder = "pickle_exports"
    if not os.path.exists(pickle_folder):
        os.makedirs(pickle_folder)
    pickle_filename = "%s/compute_score_%s_dpt%s.pickle" % (pickle_folder, current_time, departement)
    pickle.dump(pickle_data, open(pickle_filename, "wb"))

    try:
        logger.info("precision for %s: non-embauche %s, embauche %s", departement, precision[0], precision[1])
        logger.info("precision_train for %s: non-embauche %s, embauche %s", departement, precision_train[0], precision_train[1])
        logger.info("recall for %s: non-embauche %s, embauche %s", departement, recall[0], recall[1])
        logger.info("recall_train for %s: non-embauche %s, embauche %s", departement, recall_train[0], recall_train[1])
        logger.info("fscore for %s: non-embauche %s, embauche %s", departement, fscore[0], fscore[1])
        logger.info("support for %s: non-embauche %s, embauche %s", departement, support[0], support[1])
        logger.info("regression_train RMSE for %s: %s", departement, rmse_train)
        logger.info("regression_test RMSE for %s: %s", departement, rmse_test)
        if not(rmse_test < importer_settings.RMSE_MAX):
            raise_with_message("rmse_test too high : %s > %s" % (rmse_test, importer_settings.RMSE_MAX))
    except IndexError:
        logger.warning("not enough data to compute RMSE for %s", departement)

    try:
        # old deprecated score based on binary classification - we now use regression instead
        # df_final["score"] = [int(res[1] * 100) for res in clf.predict_proba(X_live)]
        df_final["score_regr"] = [res for res in regr.predict(X_live)]
        df_final["score"] = [scoring_util.get_score_from_hirings(h) for h in df_final["score_regr"]]
    except IndexError:
        # there's not a single positive instance in the whole dataset
        df_final["score"] = 0
        df_final["score_regr"] = 0
    ranges = [0, 20, 40, 60, 80, 100]
    logger.info('score distribution for %s', df_final.groupby(pd.cut(df_final.score, ranges))['score'].agg('count'))


def export(engine, df_final, departement):
    logger.debug("writing sql (%s)...", departement)

    def departement_to_str(x):
        if x["departement"] < 10:
            return "0%i" % x["departement"]
        else:
            return str(x["departement"])

    df_final['departement'] = df_final.apply(departement_to_str, axis=1)

    df_final.to_sql("etablissements_%s" % departement, engine, if_exists='replace', chunksize=10000)
    logger.debug("sql done (%s)!", departement)


def run(source_etablissement_table, dpae_table, departement, dpae_date, semester_lag=1):
    engine = sqlalchemy.create_engine(get_db_string(), poolclass=NullPool)
    result = load_df(engine, source_etablissement_table, dpae_table, departement, dpae_date)
    if result:
        logger.debug("result obtained for departement %s", departement)
        reference_date = compute_reference_date(dpae_date)
        df, _ = result
        train(df, departement, reference_date, semester_lag)

        logger.debug("fetching existing scores for %s", departement)
        df_existing_score = pd.read_sql_query(
            "select siret, score as existing_score from %s where departement=%s" % (
                importer_settings.EXPORT_ETABLISSEMENT_TABLE, departement
            ),
            engine
        )
        debug_df(df_existing_score, "df_existing_score")
        if df_existing_score.empty:
            logger.debug("no scores for now for departement %s, bypassing score regression...", departement)
        else:
            logger.debug("merging existing scores for %s", departement)
            # merge doc : http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.merge.html
            # by default how='inner' use intersection of keys from both frames (SQL: inner join)
            # what we need here is how=left: use only keys from left frame (SQL: left outer join)
            # because we keep all companies from current extract, whether or not they were present before
            debug_df(df, "before merge with df_existing_score")
            df = pd.merge(df, df_existing_score, on="siret", how="left")
            debug_df(df, "after merge with df_existing_score and how=left")
            df["diff_score"] = df["score"] - df["existing_score"]
            logger.info(
                "mean difference of scores: %s new score %s existing score %s",
                df[["diff_score"]].mean()[0],
                df[["score"]].mean()[0],
                df[["existing_score"]].mean()[0]
            )
            # abort if the mean between the existing score and the new just computed score is too high
            check_mean_between_existing_and_new_score(departement, df)

            high_existing_scores = df[df["existing_score"] > 50]["siret"].count()
            high_new_scores = df[df["score"] > 50]["siret"].count()
            logger.info("existing high scores > 50: %s", high_existing_scores)
            logger.info("new high scores > 50: %s", high_new_scores)
            # abort if the number of highly scored companies varies much
            check_highly_scored_companies_evolution(departement, high_existing_scores, high_new_scores)
            check_number_highly_scored_companies(departement, high_new_scores)

            logger.debug("merging done (%s)!", departement)

        export(engine, df, departement)
    else:
        logger.warn("no result for departement %s", departement)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG
    )
    most_recent_data_date = DpaeStatistics.get_most_recent_data_date()
    run(importer_settings.OFFICE_TABLE, importer_settings.DPAE_TABLE, sys.argv[1], most_recent_data_date, semester_lag=1)
