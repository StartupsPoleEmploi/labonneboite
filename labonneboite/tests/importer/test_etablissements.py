from labonneboite.importer.models.computing import RawOffice
from labonneboite.importer.jobs.extract_etablissements import EtablissementExtractJob, normalize_website_url
from .test_base import DatabaseTest


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

ETABLISSEMENT_FILE = "lbb_etablissement_full_201612192300.csv"

class TestEtablissements(DatabaseTest):

    def test_get_sirets_from_database(self):
        filename = self.get_data_file_path(ETABLISSEMENT_FILE)
        task = EtablissementExtractJob(filename)
        etabs = task.get_sirets_from_database()
        self.assertEqual(len(etabs), 0)
        make_raw_office()
        etabs = task.get_sirets_from_database()
        self.assertEqual(len(etabs), 1)
        self.assertEqual(etabs[0], "12345678901234")

    def test_get_offices_from_file(self):
        filename = self.get_data_file_path(ETABLISSEMENT_FILE)
        task = EtablissementExtractJob(filename)
        etabs = task.get_offices_from_file()
        self.assertEqual(len(list(etabs.keys())), 26)
        _, raisonsociale, _, _, _, _, \
        _, _, email, _, _, _, \
        _, _, _ = etabs.get('26560004900167').get('create_fields')
        self.assertEqual(raisonsociale, 'CTRE HOSPITALIER JOSSELIN')
        self.assertEqual(email, '')
        _, raisonsociale, _, _, _, _, \
        _, _, email, _, _, _, \
        _, _, _ = etabs.get('26560004900267').get('create_fields')
        self.assertEqual(raisonsociale, 'POLE EMPLOI')
        self.assertEqual(email, 'origin_email@pole-emploi.fr')

    def test_create_new_offices(self):
        filename = self.get_data_file_path(ETABLISSEMENT_FILE)
        task = EtablissementExtractJob(filename)
        task.csv_offices = task.get_offices_from_file()
        task.creatable_sirets = [
            "00565014800033", "00685016800011"
        ]
        task.create_creatable_offices()
        self.assertEqual(len(RawOffice.query.all()), 2)

    def test_delete_offices(self):
        filename = self.get_data_file_path(ETABLISSEMENT_FILE)
        task = EtablissementExtractJob(filename)
        task.csv_offices = task.get_offices_from_file()
        task.creatable_sirets = [
            "00565014800033", "00685016800011"
        ]
        task.create_creatable_offices()
        task.deletable_sirets = set(["00565014800033"])
        task.delete_deletable_offices()
        self.assertEqual(len(RawOffice.query.all()), 1)
        self.assertEqual(RawOffice.query.first().siret, "00685016800011")

    def test_normalize_url(self):
        self.assertEqual(normalize_website_url(None), None)
        self.assertEqual(normalize_website_url(''), None)
        self.assertEqual(normalize_website_url('abc'), None)
        self.assertEqual(normalize_website_url('abc.com'), 'http://abc.com')
        self.assertEqual(normalize_website_url('abc.fr'), 'http://abc.fr')
        self.assertEqual(normalize_website_url('http://abc.fr'), 'http://abc.fr')
        self.assertEqual(normalize_website_url('https://abc.fr'), 'https://abc.fr')
        self.assertEqual(normalize_website_url('abc@def.fr'), None)

    def test_emails_rgpd(self):
        filename = self.get_data_file_path(ETABLISSEMENT_FILE)
        task = EtablissementExtractJob(filename)
        etabs = task.get_offices_from_file()

        _, _, _, _, _, _, \
        _, _, email, _, _, _, \
        _, _, _ = etabs.get('00565014800033').get('create_fields')
        self.assertEqual(email, 'laf2@example.eu') #The office has 2 emails, and the rgpd email is the main

        _, _, _, _, _, _, \
        _, _, email, _, _, _, \
        _, _, _ = etabs.get('48874364200024').get('create_fields')
        self.assertEqual(email, 'f.renier@abcdef.tm.fr') #The office has only one email, no rgpd

        _, _, _, _, _, _, \
        _, _, email, _, _, _, \
        _, _, _ = etabs.get('42086672500021').get('create_fields')
        self.assertEqual(email, 'frederic.fleury@abcdef.fr') #The office has only one email, rgpd
