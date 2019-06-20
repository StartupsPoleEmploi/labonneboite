from labonneboite.importer.models.computing import ExportableOffice
from labonneboite.importer.jobs.geocode import GeocodeJob
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

    def test_run_geocoding_job(self):
        task = GeocodeJob()
        initial_coordinates = [0, 0]
        jobs = [[1234, "1 rue Marca 64000 Pau", initial_coordinates, '64445']]
        task.run_geocoding_jobs(jobs)
        updates = task.run_missing_geocoding_jobs()
        self.assertTrue(len(updates), 1)
        coordinates = updates[0][1]
        self.assertEqual(int(coordinates[0]), 0)
        self.assertEqual(int(coordinates[1]), 43)

    def test_run_geocoding_jobs(self):
        task = GeocodeJob()
        initial_coordinates = [0, 0]
        jobs = [['001234', "1 rue Marca 64000 Pau", initial_coordinates, '64445'],
                ['005678', "13 rue de l'hotel de ville 44000 Nantes", initial_coordinates, '44109']]
        task.run_geocoding_jobs(jobs)
        updates = task.run_missing_geocoding_jobs(csv_max_rows=1)
        self.assertTrue(len(updates), 2)
        coordinates_1 = updates[0]
        coordinates_2 = updates[1]
        # We want to test this because we had an issue, where the pandas dataframes changes types of siret to int, and the '00' at the start of siret was removed
        self.assertTrue(len(coordinates_1[0]), 6)
        # Multithreading may switch order of coordinates, so we have to check which siret is returned, to see what coordinates we want to check
        if coordinates_1[0] == '001234':
            self.assertEqual(int(coordinates_1[1][0]), 0)
            self.assertEqual(int(coordinates_1[1][1]), 43)
            self.assertEqual(int(coordinates_2[1][0]), -1)
            self.assertEqual(int(coordinates_2[1][1]), 47)
        else:
            self.assertEqual(int(coordinates_1[1][0]), -1)
            self.assertEqual(int(coordinates_1[1][1]), 47)
            self.assertEqual(int(coordinates_2[1][0]), 0)
            self.assertEqual(int(coordinates_2[1][1]), 43)

    def test_create_geocoding_jobs(self):
        task = GeocodeJob()
        jobs = task.create_geocoding_jobs()
        self.assertEqual(len(jobs), 0)
        make_geocoded_office()
        jobs = task.create_geocoding_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0][0], "1234")
        self.assertEqual(
            jobs[0][1], "30 rue Edouard Poisson 93300 AUBERVILLIERS")

    def test_update_coordinates(self):
        make_geocoded_office()
        task = GeocodeJob()
        updates = [["1234", [0, 43]]]
        task.update_coordinates(updates)
        office = ExportableOffice.query.first()
        self.assertEqual(int(office.x), 0)
        self.assertEqual(int(office.y), 43)
