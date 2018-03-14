from labonneboite.importer.models.computing import RawOffice
from labonneboite.importer.jobs.extract_etablissements import EtablissementExtractJob
from labonneboite.importer.tests.test_base import DatabaseTest


def make_raw_office():
    office = RawOffice(
        siret="12345678901234",
        company_name="SNCF",
        street_number="30",
        street_name="rue Edouard Poisson",
        zipcode="93300",
        city_code="93001",
        departement="57",
        headcount="11",
        naf="2363Z",
    )
    office.save()


class TestEtablissements(DatabaseTest):

    def test_get_sirets_from_database(self):
        filename = self.get_data_file_path("LBB_EGCEMP_ENTREPRISE_20151119_20161219_20161219_153447.csv")
        task = EtablissementExtractJob(filename)
        etabs = task.get_sirets_from_database()
        self.assertEquals(len(etabs), 0)
        make_raw_office()
        etabs = task.get_sirets_from_database()
        self.assertEquals(len(etabs), 1)
        self.assertEquals(etabs[0], "12345678901234")

    def test_get_offices_from_file(self):
        filename = self.get_data_file_path("LBB_EGCEMP_ENTREPRISE_20151119_20161219_20161219_153447.csv")
        task = EtablissementExtractJob(filename)
        etabs = task.get_offices_from_file()
        self.assertEquals(len(etabs.keys()), 24)

    def test_create_new_offices(self):
        filename = self.get_data_file_path("LBB_EGCEMP_ENTREPRISE_20151119_20161219_20161219_153447.csv")
        task = EtablissementExtractJob(filename)
        task.csv_offices = task.get_offices_from_file()
        task.creatable_sirets = [
            "00565014800033", "00685016800011"
        ]
        task.create_creatable_offices()
        self.assertEquals(len(RawOffice.query.all()), 2)

    def test_delete_offices(self):
        filename = self.get_data_file_path("LBB_EGCEMP_ENTREPRISE_20151119_20161219_20161219_153447.csv")
        task = EtablissementExtractJob(filename)
        task.csv_offices = task.get_offices_from_file()
        task.creatable_sirets = [
            "00565014800033", "00685016800011"
        ]
        task.create_creatable_offices()
        task.deletable_sirets = set(["00565014800033"])
        task.delete_deletable_offices()
        self.assertEquals(len(RawOffice.query.all()), 1)
        self.assertEquals(RawOffice.query.first().siret, "00685016800011")
