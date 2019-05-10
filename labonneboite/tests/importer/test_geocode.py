from labonneboite.importer.models.computing import ExportableOffice
from labonneboite.importer.jobs.geocode import GeocodeJob
from labonneboite.importer.jobs.geocode import GeocodeUnit
from .test_base import DatabaseTest


def make_geocoded_office():
    office = ExportableOffice(
        siret=1234,
        company_name="SNCF",
        street_number="30",
        street_name="rue Edouard Poisson",
        zipcode="93300",
        city_code="93001",
        departement="57",
        headcount="11",
        naf="2363Z",
        x=1.1,
        y=1.1,
    )
    office.save()


class TestGeocode(DatabaseTest):

    #TODO Question : Do I need to make other tests for geocoding ?

    def test_run_geocoding_jobs(self):
        task = GeocodeJob()
        initial_coordinates = [0, 0]
        jobs = [[1234, "1 rue Marca 64000 Pau", initial_coordinates, '64445']]
        task.run_geocoding_jobs(jobs)
        updates = task.run_missing_geocoding_jobs()
        self.assertTrue(len(updates), 1)
        coordinates = updates[0][1]
        self.assertEqual(int(coordinates[0]), 0)
        self.assertEqual(int(coordinates[1]), 43)

    def test_create_geocoding_jobs(self):
        task = GeocodeJob()
        jobs = task.create_geocoding_jobs()
        self.assertEqual(len(jobs), 0)
        make_geocoded_office()
        jobs = task.create_geocoding_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0][0], "1234")
        self.assertEqual(jobs[0][1], "30 rue Edouard Poisson 93300 AUBERVILLIERS")

    def test_update_coordinates(self):
        make_geocoded_office()
        task = GeocodeJob()
        updates = [["1234", [0, 43]]]
        task.update_coordinates(updates)
        office = ExportableOffice.query.first()
        self.assertEqual(int(office.x), 0)
        self.assertEqual(int(office.y), 43)
