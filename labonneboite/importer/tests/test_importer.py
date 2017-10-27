from labonneboite.importer import sanity
from labonneboite.common.models import Office
from labonneboite.importer.tests.test_base import DatabaseTest


def make_office(departement="04", siret="1234", score=60):
    office = Office(departement=departement, siret=siret, score=score)
    return office


class TestSanity(DatabaseTest):

    def test_check_succeeds(self):
        office = make_office()
        office.save()
        errors = sanity.check_scores(departements=["04",], minimum_office_count=1)
        self.assertEquals(len(errors), 0)

    def test_check_other_departement_fails(self):
        office = make_office()
        office.save()
        errors = sanity.check_scores(departements=["03",], minimum_office_count=1)
        self.assertEquals(len(errors), 1)

    def test_check_low_score_fails(self):
        office = make_office(score=40)
        office.save()
        errors = sanity.check_scores(departements=["04",], minimum_office_count=1)
        self.assertEquals(len(errors), 1)
