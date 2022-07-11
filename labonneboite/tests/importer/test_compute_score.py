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

    def test_unhappy_path(self):
        make_offices()
        make_hirings()
        departement = "58"
        prediction_beginning_date = get_prediction_beginning_date()
        result = compute_score.run(departement, prediction_beginning_date)
        self.assertEqual(result, False)  # failed computation (no data for this departement)
