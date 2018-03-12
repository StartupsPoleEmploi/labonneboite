from datetime import datetime, timedelta
import random

from labonneboite.importer import compute_score
from labonneboite.importer import settings
from labonneboite.importer.models.computing import Dpae, RawOffice
from .test_base import DatabaseTest


def make_office():
    for i in range(0, 200):
        office = RawOffice(departement="57", siret=str(i), headcount="03", company_name="SNCF",
            naf="2363Z", city_code="57463", zipcode="57000")
        office.save()


def make_dpae():
    # 500 dpaes are randomly attached to first 100 of 200 existing offices
    now = datetime.now()
    random.seed(99)  # use a seed to get deterministic random numbers
    for i in range(0, 500):
        dpae_date = now - timedelta(days=i * 10)
        dpae = Dpae(
            siret=str(random.randint(0, 100)),
            departement="57",
            contract_type=1,
            hiring_date=dpae_date,
        )
        dpae.save()


class TestComputeScore(DatabaseTest):

    def test_happy_path(self):
        make_office()
        make_dpae()
        dpae_date = datetime.now()
        departement = "57"
        compute_score.run(settings.RAW_OFFICE_TABLE, settings.DPAE_TABLE, departement, dpae_date)

    def test_normalize_url(self):
        self.assertEqual(compute_score.normalize_website_url(None), None)
        self.assertEqual(compute_score.normalize_website_url(''), None)
        self.assertEqual(compute_score.normalize_website_url('abc'), None)
        self.assertEqual(compute_score.normalize_website_url('abc.com'), 'http://abc.com')
        self.assertEqual(compute_score.normalize_website_url('abc.fr'), 'http://abc.fr')
        self.assertEqual(compute_score.normalize_website_url('http://abc.fr'), 'http://abc.fr')
        self.assertEqual(compute_score.normalize_website_url('https://abc.fr'), 'https://abc.fr')
        self.assertEqual(compute_score.normalize_website_url('abc@def.fr'), None)
