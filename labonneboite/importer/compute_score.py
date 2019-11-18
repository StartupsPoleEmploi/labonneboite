# coding: utf-8
"""Machine learning module.

The outside world uses the "run" function which will predict how many hirings
a company will make in the next period
(i.e. 6 months for DPAE and 6 months for Alternance as well)
and we use a regression model to do so.

The predicted number of hirings is
then transformed and obfuscated into a "score" value
between 0 and 100 for each office ("etablissement").

We do this because we consider the predicted number of hirings to be a 
sensitive confidential data, this way, by storing only the obfuscated score in db,
even if our db gets hacked you cannot transform the score back into their
corresponding predicted number of hirings.

We train a machine learning algorithm on companies and employment data to predict
the number of hirings.

We use the scikit-learn library: more info at
http://scikit-learn.org/stable/documentation.html
"""
from calendar import monthrange
import math
from operator import getitem
import os
import pickle
import sys

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import pandas as pd
import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error
import sqlalchemy
from sqlalchemy.pool import NullPool
from labonneboite.common.util import timeit
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.models.computing import DpaeStatistics, Hiring, RawOffice
from labonneboite.common import scoring as scoring_util
from labonneboite.common.database import get_db_string
from labonneboite.common.env import get_current_env, ENV_DEVELOPMENT
from .debug import listen
from .jobs.common import logger

listen()

def get_engine():
    return sqlalchemy.create_engine(get_db_string(), poolclass=NullPool)

# Output additional debug info about these sirets
# To disable, set to an empty list []
# Sirets must be string, not int
DEBUG_SIRETS = ["19240023200018", "33530956300047", "26760168000015"]
# DEBUG_SIRETS = []

# disable unnecessary pandas SettingWithCopyWarning
# see http://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
# default value is 'warn'
pd.options.mode.chained_assignment = None


class NotEnoughDataException(Exception):
    pass


def raise_with_message(msg):
    logger.info("WARNING exception: %s", msg)
    raise Exception(msg)


def debug_df(df, description="no description"):
    """
    Outputs useful information about dataframe
    """
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


def check_coefficient_of_variation(df_etab, departement, period_count_columns, prefix):
    hiring_count_per_period_sum = df_etab[period_count_columns].sum(axis=0)
    coefficient_of_variation = hiring_count_per_period_sum.std() / hiring_count_per_period_sum.mean()
    logger.debug('hiring_count_per_period_sum %s', hiring_count_per_period_sum)
    logger.debug('coefficient of variation of hiring count per period %s', coefficient_of_variation)
    logger.info("checking mean_between_existing_and_new_score: %s", coefficient_of_variation)
    if not discarded_check(departement):
        if not coefficient_of_variation < importer_settings.SCORE_COEFFICIENT_OF_VARIATION_MAX:
            raise_with_message("[dpt%s] %s coefficient_of_variation too high: %s > %s" % (
                departement,
                prefix,
                coefficient_of_variation,
                importer_settings.SCORE_COEFFICIENT_OF_VARIATION_MAX
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
            raise_with_message(
                "evolution too high: %s > %s" % (evolution, importer_settings.HIGH_SCORE_COMPANIES_DIFF_MAX)
            )


def check_number_highly_scored_companies(departement, high_new_scores):
    if not discarded_check(departement):
        if not high_new_scores > importer_settings.HIGH_SCORE_COMPANIES_COUNT_MIN:
            error_msg = "high_new_scores too low: %s < %s" % (
                high_new_scores,
                importer_settings.HIGH_SCORE_COMPANIES_COUNT_MIN
            )
            raise Exception(error_msg)


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
    if tranche not in list(map_tranche_to_effectif.keys()):
        return 1
    return map_tranche_to_effectif[tranche]


def check_prediction_beginning_date(prediction_beginning_date):
    if prediction_beginning_date.day != 1:
        raise ValueError("prediction_beginning_date should be the first day of the month")


def check_last_historical_data_date(last_historical_data_date):
    # last day of the month == next day is first day of the month
    if (last_historical_data_date + timedelta(days=1)).day != 1:
        raise ValueError("last_historical_data_date should be the last day of the month")


def go_back_last_day_of_the_month(date):
    if (date + timedelta(days=1)).day == 1:
        return date  # already a last day of the month
    first_day_of_the_month = date.replace(day=1)
    return first_day_of_the_month - timedelta(days=1)  # last day of previous month


@timeit
def get_df_etab(departement):
    logger.debug("reading etablissements data (%s)", departement)
    df_etab = pd.read_sql_query("""
        select * from %s where departement = %s and siret != ''
        """ % (RawOffice.__tablename__, departement), get_engine())
    debug_df(df_etab, "after loading from raw office table")
    if df_etab.empty:
        logger.warning("dataframe empty for departement %s", departement)
        return None
    logger.debug("loading data (%s) OK (%i etablissements)!", departement, len(df_etab))

    logger.debug("adding effectif (%s)...", departement)
    df_etab['effectif'] = df_etab['trancheeffectif'].map(tranche_to_effectif)
    logger.debug("effectif done (%s)!", departement)

    return df_etab


@timeit
def get_df_hiring(departement, prediction_beginning_date):
    logger.debug("reading hiring data...")
    df_hiring = pd.read_sql_query("""
        select
            siret,
            hiring_date,
            case
                when contract_type in (%s) then 'dpae'
                when contract_type in (%s) then 'alt'
            end as hiring_type
        from %s
        where
            departement = %s
            and contract_type in (%s)
            and hiring_date < '%s'
        """ % (
            ', '.join([str(c_t) for c_t in Hiring.CONTRACT_TYPES_DPAE]),
            ', '.join([str(c_t) for c_t in Hiring.CONTRACT_TYPES_ALTERNANCE]),
            Hiring.__tablename__,
            departement,
            ', '.join([str(c_t) for c_t in Hiring.CONTRACT_TYPES_ALL]),
            str(prediction_beginning_date.isoformat()),
        ),
        get_engine(),
    )
    debug_df(df_hiring, "after loading from hiring table")
    if df_hiring.empty:
        logger.warning("no hiring data for departement %s", departement)
        return None

    df_hiring["hiring_date_month"] = pd.DatetimeIndex(df_hiring["hiring_date"]).month
    df_hiring["hiring_date_year"] = pd.DatetimeIndex(df_hiring["hiring_date"]).year

    return df_hiring


@timeit
def get_df_etab_with_hiring_monthly_aggregates(departement, prediction_beginning_date):
    """
    Returns a df_etab dataframe
    with one row per siret and one column per month (hirings total for given month)
    for all (past) months before (now) prediction_beginning_date.
    """
    df_etab = get_df_etab(departement)  # has one row per siret

    df_dpae = get_df_hiring(departement, prediction_beginning_date)  # has one row per hiring

    if df_etab is None or df_dpae is None:
        return None

    df_dpae = df_dpae.groupby(["siret", "hiring_type", "hiring_date_year", "hiring_date_month"]).count().reset_index()
    debug_df(df_dpae, "after group by")
    logger.debug("pivoting table dpae (%s)...", departement)
    # FIXME understand why `values="hiring_date"` is needed at all
    df_dpae = pd.pivot_table(df_dpae, values="hiring_date", index="siret",
        columns=["hiring_type", "hiring_date_year", "hiring_date_month"])
    debug_df(df_dpae, "after pivot")
    logger.debug("pivoting table (%s) ok!", departement)

    # after this pivoting,
    # df_dpae has one row per siret and one column per month (hirings total for given month)
    # and per hiring_type

    df_dpae["siret"] = df_dpae.index
    df_dpae = df_dpae.fillna(0)

    df_dpae.columns = ['-'.join([str(c) for c in col]) for col in df_dpae.columns.values]
    siret_raw_column_name = 'siret--'
    df_dpae['siret'] = df_dpae[siret_raw_column_name]
    del df_dpae[siret_raw_column_name]
    debug_df(df_dpae, "after transform")

    #### joining hiring and etab

    # at this moment
    # df_etab has one row per siret
    # df_dpae has one row per siret and one column per month (hirings total for given month)
    # and per hiring_type

    logger.debug("merging dpae with etablissements (%s)...", departement)
    # inner join to keep only etabs which have at least one dpae
    df_etab = pd.merge(df_dpae, df_etab, on='siret', how="inner")
    debug_df(df_etab, "after merge")
    logger.debug("merging done with %s offices(%s)!", len(df_etab), departement)

    # after this inner joining,
    # df_etab has one row per siret and one column per month (hirings total for given month)
    # and per hiring_type

    if "website" not in list(df_etab.columns):
        raise Exception("missing website column")

    df_etab = df_etab.fillna(0)

    return df_etab


def compute_prediction_beginning_date():
    """
    We predict hirings starting from the 1st of the current month.
    """
    now = datetime.now()
    prediction_beginning_date = now.replace(day=1)  # get 1st of the month
    logger.info("prediction_beginning_date = %s", prediction_beginning_date)
    return prediction_beginning_date


def total_hired_period(period):
    def f(office):
        return office[period]
    return f


# from https://stackoverflow.com/questions/7015587/python-difference-of-2-datetimes-in-months
def months_between_dates(d1, d2):
    delta = 0
    while True:
        mdays = monthrange(d1.year, d1.month)[1]
        d1 += timedelta(days=mdays)
        if d1 <= d2:
            delta += 1
        else:
            break
    return delta


def get_features_for_lag(df_etab, prefix, training_periods, data_gap_in_periods,
        periods_back_in_time, debug_msg="Unnamed"):
    temporal_features = []
    for i in range(0, training_periods):  # [0, 1, ... training_periods - 1]
        index = data_gap_in_periods + (1 + i) + periods_back_in_time
        temporal_features.append('%s-period-%i' % (prefix, index))
    features = list(temporal_features)
    features.append('effectif')

    df_etab_features_only = df_etab[features]
    X = df_etab_features_only.values

    df_etab_for_debug = df_etab[["siret"] + features]
    debug_df(df_etab_for_debug, debug_msg)

    return X, features


def get_hirings_over_period_for_office(office, prediction_beginning_date, months_per_period, minus, prefix):
    """
    office : one row of df_etab.
    minus : how many periods to go back in time.
    """
    start_date = prediction_beginning_date + relativedelta(months=-(months_per_period * minus))

    columns_of_period = []
    for i in range(0, months_per_period):  # [0, 1, 2, ..., months_per_period - 1]
        current_date = start_date + relativedelta(months=i)
        columns_of_period.append('%s-%s-%s' % (prefix, current_date.year, current_date.month))

    hirings_over_period = 0
    for column in columns_of_period:
        try:
            hirings_over_period += getitem(office, column)
        except KeyError:
            pass

    return hirings_over_period


def compute_hiring_aggregates(
        df_etab, departement, prediction_beginning_date, periods, prefix, months_per_period):
    """
    Edits in place df_etab.
    Adds one column per period containing hiring total for this hiring_type.
    """
    logger.debug("computing %s hiring aggregates (%s)...", prefix, departement)

    # df_etab has one row per siret and one column per hiring month-aggregate and per hiring_type
    period_count_columns = []
    for i in range(1, periods + 1):  # [1, 2, ..., periods]
        column = '%s-period-%s' % (prefix, i)
        # pylint: disable=cell-var-from-loop
        df_etab[column] = df_etab.apply(
            lambda office: get_hirings_over_period_for_office(
                office, prediction_beginning_date, months_per_period, minus=i, prefix=prefix,
            ),
            axis=1,
        )
        period_count_columns.append(column)
    logger.debug("finished calculating %s temporal features (%s)!", prefix, departement)

    check_coefficient_of_variation(df_etab, departement, period_count_columns, prefix)

    debug_df(df_etab, "df_etab after compute_hiring_aggregates")


@timeit
def train(df_etab, departement, prediction_beginning_date, last_historical_data_date,
        months_per_period, training_periods, prefix_for_fields, score_field_name):
    """
    Edits in place df_etab by adding final score columns
    (e.g. score and score_regr for DPAE/LBB, or score_alternance and score_alternance_regr for LBA).
    
    TODO we should trash the score and score_alternance legacy columns
    since they come from legacy binary classification model and are no longer
    used. We now only use score_regr and score_alternance_regr computed
    by the regression model.

    At the beginning of this method, df_etab has one row per siret and one column per month and
    per hiring_type.

    At the end of this method df_etab has one row per siret and one column per hiring_type and
    per period (hirings total for given period).
    """
    check_prediction_beginning_date(prediction_beginning_date)
    check_last_historical_data_date(last_historical_data_date)

    data_gap_in_months = months_between_dates(last_historical_data_date, prediction_beginning_date)
    # math.ceil returns a float and not an int, thus we still need to cast it to int.
    # `1.0 * int/int` trick is needed because otherwise int/int gives the floor int value.
    data_gap_in_periods = int(math.ceil(data_gap_in_months / months_per_period))

    if prefix_for_fields == "dpae":
        if get_current_env() == ENV_DEVELOPMENT:
            if data_gap_in_periods <= 0:
                raise ValueError("dpae data should have at least one period of gap")
        else:
            #if data_gap_in_periods != 0:
            if data_gap_in_periods not in [0, 1]:
                # FIXME restore when we have dpae 10 april
                raise ValueError("dpae data should have no gap")
    if prefix_for_fields == "alt":
        if data_gap_in_periods <= 0:
            raise ValueError("alternance data should have at least one month of gap")

    # Training set is moved 2 years back in time relative to live set,
    # and testing set is moved 1 year back in time relative to live set.
    # To understand why check
    # https://docs.google.com/document/d/1-UqC8wZBhHEgMvzMi0SQamnXvkU6itLwubZiI00yH6E/edit
    periods_per_year = 12 // months_per_period
    total_periods = training_periods + 2 * periods_per_year + data_gap_in_periods

    # add in place hiring aggregates per period
    compute_hiring_aggregates(
        df_etab,
        departement,
        prediction_beginning_date,
        periods=total_periods,
        prefix=prefix_for_fields,
        months_per_period=months_per_period,
    )

    # We model the problem as a linear regression.
    regr = linear_model.LinearRegression()

    y_train_period = '%s-period-%s' % (prefix_for_fields, 2 * periods_per_year)
    y_train_regr = df_etab.apply(total_hired_period(y_train_period), axis=1)

    X_train, X_train_feature_names = get_features_for_lag(
        df_etab,
        prefix_for_fields,
        training_periods,
        data_gap_in_periods,
        periods_back_in_time=2 * periods_per_year,
        debug_msg="X_train",
    )

    logger.debug("(%s %s) %s offices", departement, prefix_for_fields, len(df_etab))

    if len(df_etab) < importer_settings.MINIMUM_OFFICES_REQUIRED_TO_TRAIN_MODEL:
        # problems happen if we don't have enough offices to train on...
        # throw an exception to show we don't have enough data for this departement
        raise NotEnoughDataException("only %s offices !" % len(df_etab))
    logger.debug("(%s %s) fitting the model on X_train...", departement, prefix_for_fields)
    regr.fit(X_train, y_train_regr)
    logger.debug("(%s %s) fitting done!", departement, prefix_for_fields)

    logger.debug("(%s %s) X_train_feature_names: %s", departement, prefix_for_fields, X_train_feature_names)
    logger.debug("(%s %s) regression_coefficients (fitting done on X_train) : %s",
        departement, prefix_for_fields, regr.coef_)

    X_test, X_test_feature_names = get_features_for_lag(
        df_etab,
        prefix_for_fields,
        training_periods,
        data_gap_in_periods,
        periods_back_in_time=periods_per_year,
        debug_msg="X_test",
    )

    logger.debug("(%s %s) X_test_feature_names: %s", departement, prefix_for_fields, X_test_feature_names)

    X_live, X_live_feature_names = get_features_for_lag(
        df_etab,
        prefix_for_fields,
        training_periods,
        data_gap_in_periods,
        periods_back_in_time=0,
        debug_msg="X_live",
    )

    logger.debug("(%s %s) X_live_feature_names: %s", departement, prefix_for_fields, X_live_feature_names)

    # --- compute regression metrics
    y_train_regr_pred = regr.predict(X_train)
    y_test_period = '%s-period-%s' % (prefix_for_fields, periods_per_year)
    y_test_regr = df_etab.apply(total_hired_period(y_test_period), axis=1)
    y_test_regr_pred = regr.predict(X_test)
    rmse_train = mean_squared_error(y_train_regr, y_train_regr_pred)
    rmse_test = mean_squared_error(y_test_regr, y_test_regr_pred)
    # --- end of regression metrics

    pickle_data = {
        "departement": departement,
        "X_train_feature_names": X_train_feature_names,
        "X_test_feature_names": X_test_feature_names,
        "X_live_feature_names": X_live_feature_names,
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
        logger.info("(%s %s) regression_train RMSE : %s", departement, prefix_for_fields, rmse_train)
        logger.info("(%s %s) regression_test RMSE : %s", departement, prefix_for_fields, rmse_test)
        if rmse_test >= importer_settings.RMSE_MAX:
            raise_with_message("rmse_test too high : %s > %s" % (rmse_test, importer_settings.RMSE_MAX))
    except IndexError:
        logger.warning("not enough data to compute RMSE for %s", departement)

    score_regr_field_name = "%s_regr" % score_field_name

    df_etab[score_regr_field_name] = regr.predict(X_live)
    df_etab[score_field_name] = [scoring_util.get_score_from_hirings(h) for h in df_etab[score_regr_field_name]]

    ranges = [0, 20, 40, 60, 80, 100]
    logger.info('(%s %s) score distribution : %s', departement, prefix_for_fields,
        df_etab.groupby(pd.cut(df_etab.score, ranges))[score_field_name].agg('count'))

    compare_new_scores_to_old_ones(departement, df_etab)


@timeit
def export_df_etab_to_db(df_etab, departement):
    logger.debug("writing sql (%s)...", departement)

    def departement_to_str(x):
        return "{:02d}".format(int(x["departement"]))

    df_etab['departement'] = df_etab.apply(departement_to_str, axis=1)

    # FIXME control more precisely the schema (indexes!) of temporary tables created by to_sql,
    # current version adds an 'index' column (which is the panda dataframe index column itself,
    # nothing to do with our app) and makes it a primary key.
    # see https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_sql.html
    # Maybe using no index at all (no primary key) would be faster.
    df_etab.to_sql("etablissements_%s" % departement, get_engine(), if_exists='replace', chunksize=10000)
    logger.debug("sql done (%s)!", departement)


@timeit
def compare_new_scores_to_old_ones(departement, df_etab):
    logger.debug("fetching existing scores for %s", departement)
    df_existing_score = pd.read_sql_query(
        "select siret, score as existing_score from %s where departement=%s" % (
            importer_settings.SCORE_REDUCING_TARGET_TABLE, departement
        ),
        get_engine(),
    )
    debug_df(df_existing_score, "df_existing_score")
    if df_existing_score.empty:
        logger.debug("no old score found for departement %s, skipping old/new score comparison...", departement)
    else:
        logger.debug("merging existing scores for %s", departement)
        # merge doc : http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.merge.html
        # by default how='inner' use intersection of keys from both dataframes (SQL: inner join)
        # what we need here is how='left': use only keys from left dataframe (SQL: left outer join)
        # because we keep all companies from current extract, whether or not they were present before
        debug_df(df_etab, "before merge with df_existing_score")
        df_etab = pd.merge(df_etab, df_existing_score, on="siret", how="left")
        debug_df(df_etab, "after merge with df_existing_score and how=left")
        df_etab["diff_score"] = df_etab["score"] - df_etab["existing_score"]
        logger.info(
            "mean difference of scores: %s new score %s existing score %s",
            df_etab[["diff_score"]].mean()[0],
            df_etab[["score"]].mean()[0],
            df_etab[["existing_score"]].mean()[0]
        )
        # abort if the mean between the existing score and the new just computed score is too high
        check_mean_between_existing_and_new_score(departement, df_etab)

        high_existing_scores = df_etab[df_etab["existing_score"] > 50]["siret"].count()
        high_new_scores = df_etab[df_etab["score"] > 50]["siret"].count()
        logger.info("existing high scores > 50: %s", high_existing_scores)
        logger.info("new high scores > 50: %s", high_new_scores)
        # abort if the number of highly scored companies varies much
        check_highly_scored_companies_evolution(departement, high_existing_scores, high_new_scores)
        check_number_highly_scored_companies(departement, high_new_scores)


@timeit
def run(
        departement,
        prediction_beginning_date=compute_prediction_beginning_date(),
        return_df_etab_if_successful=False,
    ):
    """
    Returns True if computation successful and False otherwise.
    """

    check_prediction_beginning_date(prediction_beginning_date)
    # get df_etab with monthly hirings for each hiring_type
    # hirings are not yet grouped by period (i.e. 6 months for DPAE / 6 months for Alternance)
    df_etab = get_df_etab_with_hiring_monthly_aggregates(departement, prediction_beginning_date)
    logger.debug("df_etab_with_hiring_monthly_aggregates loaded for departement %s", departement)

    if df_etab is None:
        logger.warning("no etab/hiring data found for departement %s", departement)
        return False # failed computation (e.g. no data)

    # LBB / DPAE.

    train(
        df_etab,
        departement,
        prediction_beginning_date=prediction_beginning_date,
        last_historical_data_date=go_back_last_day_of_the_month(DpaeStatistics.get_last_historical_data_date()),
        months_per_period=6,
        training_periods=7,
        prefix_for_fields='dpae',
        score_field_name='score',
    )
    logger.debug("DPAE/LBB training done for departement %s", departement)

    # LBA / Alternance.

    train(
        df_etab,
        departement,
        prediction_beginning_date=prediction_beginning_date,
        last_historical_data_date=importer_settings.ALTERNANCE_LAST_HISTORICAL_DATA_DATE,
        months_per_period=6,
        training_periods=7,
        prefix_for_fields='alt',
        score_field_name='score_alternance',
    )
    logger.debug("Alternance/LBA training done for departement %s", departement)

    # Final data export.

    export_df_etab_to_db(df_etab, departement)
    if return_df_etab_if_successful:
        return df_etab  # only used in test_compute_score.py for inspection
    return True  # successful computation


@timeit
def run_main():
    run(departement=sys.argv[1])


if __name__ == "__main__":
    run_main()
