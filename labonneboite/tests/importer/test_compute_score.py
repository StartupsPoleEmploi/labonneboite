from datetime import timedelta, datetime
import random

from labonneboite.importer import compute_score
from labonneboite.importer import settings as importer_settings
from labonneboite.importer.models.computing import Hiring, RawOffice, DpaeStatistics
from .test_base import DatabaseTest

TOTAL_OFFICES = 20
OFFICES_HAVING_HIRINGS = 10
YEARS_OF_HIRINGS = 5
AVERAGE_HIRINGS_PER_MONTH_PER_OFFICE = 2
TOTAL_HIRINGS = AVERAGE_HIRINGS_PER_MONTH_PER_OFFICE * OFFICES_HAVING_HIRINGS * 12 * YEARS_OF_HIRINGS

def get_dpae_last_historical_data_date():
    return DpaeStatistics.get_last_historical_data_date(DpaeStatistics.DPAE)


def get_prediction_beginning_date():
    # add 35 days to the first of the month to be sure to be in next month
    prediction_beginning_date = get_dpae_last_historical_data_date().replace(day=1) + timedelta(days=35)
    # get first of the next month
    return prediction_beginning_date.replace(day=1)


def make_offices():
    for i in range(0, TOTAL_OFFICES):
        office = RawOffice(departement="57", siret=str(i), headcount="03", company_name="SNCF",
            naf="2363Z", city_code="57463", zipcode="57000")
        office.save()


def make_hirings():
    random.seed(99)  # use a seed to get deterministic random numbers
    for _ in range(0, TOTAL_HIRINGS):
        hiring_date = get_dpae_last_historical_data_date() - timedelta(days=random.randint(1, 365*YEARS_OF_HIRINGS))
        hiring = Hiring(
            siret=str(random.randint(1, OFFICES_HAVING_HIRINGS)),
            departement="57",
            contract_type=random.choice(Hiring.CONTRACT_TYPES_ALL),
            hiring_date=hiring_date,
        )
        hiring.save()


class TestComputeScore(DatabaseTest):

    def test_happy_path(self):
        make_offices()
        make_hirings()
        departement = "57"
        prediction_beginning_date = get_prediction_beginning_date()
        result = compute_score.run(departement, prediction_beginning_date)
        self.assertEqual(result, True)  # successful computation

    def test_unhappy_path(self):
        make_offices()
        make_hirings()
        departement = "58"
        prediction_beginning_date = get_prediction_beginning_date()
        result = compute_score.run(departement, prediction_beginning_date)
        self.assertEqual(result, False)  # failed computation (no data for this departement)

    def test_happy_path_investigation(self):
        make_offices()
        make_hirings()
        departement = "57"
        prediction_beginning_date = get_prediction_beginning_date()
        df_etab = compute_score.run(departement, prediction_beginning_date, return_df_etab_if_successful=True)
        columns = df_etab.columns.values

        self.assertEqual(len(df_etab), OFFICES_HAVING_HIRINGS)

        # The realistic (past) situation we simulate here is the following:
        # Today is 2012 Jan 10th (as we usually run the importer each 10 of the month)
        # thus the beggining of prediction is 2012 Jan 1st (1st of current month since we are
        # in the first half of the current month),
        # note that DPAE ends at 2011 Dec 31th,
        # and that last alternance data is at 2011 Aug 31th.
        # There is gap of several months for the alternance data, and this is what happens
        # in real life as of now :/
        self.assertEqual(get_dpae_last_historical_data_date(), datetime(2011, 12, 31))
        #self.assertEqual(importer_settings.ALTERNANCE_LAST_HISTORICAL_DATA_DATE, datetime(2011, 8, 31))
        self.assertEqual(prediction_beginning_date, datetime(2012, 1, 1))  # for both DPAE and Alternance
 
        # --- DPAE/LBB checks

        # we should have exactly 5 years of hirings including the last month (2011-12)
        self.assertNotIn('dpae-2006-12', columns)
        self.assertIn('dpae-2007-1', columns)
        self.assertIn('dpae-2011-12', columns)
        self.assertNotIn('dpae-2012-1', columns)

        # Reminder: for DPAE 1 period = 6 months.
        # We expect 7+2+2=11 (past) periods to be computed, here is why:
        # LIVE set is based on 7 last periods (i.e. number of features fed to the model).
        # TEST set is like LIVE set slided 12 months earlier,
        # and thus ignores last 2 periods and is based on 7 periods before that.
        # TRAIN set is like LIVE set slided 24 months earlier,
        # and thus ignores last 4 periods and is based on 7 periods before that.
        self.assertNotIn('dpae-period-0', columns)
        self.assertIn('dpae-period-1', columns)
        self.assertIn('dpae-period-11', columns)
        self.assertNotIn('dpae-period-12', columns)

        # final score columns
        self.assertIn('score', columns)
        self.assertIn('score_regr', columns)

        # --- Alternance/LBA checks

        # we should have exactly 5 years of hirings including the last month (2011-12)
        self.assertNotIn('alt-2006-12', columns)
        self.assertIn('alt-2007-1', columns)
        self.assertIn('alt-2011-12', columns)
        self.assertNotIn('alt-2012-1', columns)

        # Reminder: for Alternance 1 period = 6 months.
        # We expect 7+2+2+1=12 (past) periods to be computed, here is why:
        # There is a gap of 4 months between the last Alternance data and today: 2011-9,10,11,12
        # rounded up to a 1 period data gap.
        # LIVE set is based on the 7 last periods (i.e. number of features fed to the model)
        # before the 1 period of the data gap.
        # TEST set is like LIVE set slided 12 months earlier,
        # and thus ignores 2 more periods and is based on 7 periods before that.
        # TRAIN set is like LIVE set slided 24 months earlier,
        # and thus ignores 4 more periods and is based on 7 periods before that.

        self.assertNotIn('alt-period-0', columns)
        self.assertIn('alt-period-1', columns)
        self.assertIn('alt-period-11', columns)
        self.assertNotIn('alt-period-12', columns)

        # final score columns
        self.assertIn('score_alternance', columns)
        self.assertIn('score_alternance_regr', columns)


