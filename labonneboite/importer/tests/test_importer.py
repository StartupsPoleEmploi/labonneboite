from labonneboite.importer import sanity
from labonneboite.importer.models.computing import ExportableOffice
from labonneboite.importer.tests.test_base import DatabaseTest


def make_office(departement="04", siret="1234", score=60):
    office = ExportableOffice(
        siret=siret,
        company_name="SNCF",
        street_number="30",
        street_name="rue Edouard Poisson",
        zipcode="93300",
        city_code="93001",
        departement=departement,
        headcount="11",
        naf="2363Z",
        x=1.1,
        y=1.1,
        score=score,
    )
    return office


class TestSanity(DatabaseTest):

    def test_check_succeeds(self):
        office = make_office()
        office.save()
        errors = sanity.check_scores(departements=["04",])
        self.assertEquals(len(errors), 0)

    def test_check_other_departement_fails(self):
        office = make_office()
        office.save()
        errors = sanity.check_scores(departements=["03",])
        self.assertEquals(len(errors), 1)

    def test_check_low_score_fails(self):
        office = make_office(score=40)
        office.save()
        errors = sanity.check_scores(departements=["04",])
        self.assertEquals(len(errors), 1)
