from labonneboite.common.models import Office
from labonneboite.importer.jobs.geocode import GeocodeJob
from labonneboite.importer.jobs.geocode import GeocodeUnit
from labonneboite.importer.tests.test_base import DatabaseTest


def make_geocoded_office():
    office = Office(
        siret=1234,
        street_number="30",
        street_name="rue Edouard Poisson",
        zipcode="93300",
        city_code="93001",
        x=1.1,
        y=1.1,
        headcount="11",
    )
    office.save()


class TestGeocode(DatabaseTest):

    def test_one(self):
        siret = 1234
        address = "1 rue Marca 64000 Pau"
        updates = []
        initial_coordinates = [0, 0]
        unit = GeocodeUnit(siret, address, updates, initial_coordinates)
        unit.find_coordinates_for_address()
        self.assertTrue(len(updates), 1)
        coordinates = updates[0][1]
        self.assertEquals(int(coordinates[0]), 0)
        self.assertEquals(int(coordinates[1]), 43)

    def test_run_geocoding_jobs(self):
        task = GeocodeJob()
        initial_coordinates = [0, 0]
        jobs = [[1234, "1 rue Marca 64000 Pau", initial_coordinates]]
        updates = task.run_geocoding_jobs(jobs)
        self.assertTrue(len(updates), 1)
        coordinates = updates[0][1]
        self.assertEquals(int(coordinates[0]), 0)
        self.assertEquals(int(coordinates[1]), 43)

    def test_create_geocoding_jobs(self):
        task = GeocodeJob()
        jobs = task.create_geocoding_jobs()
        self.assertEquals(len(jobs), 0)
        make_geocoded_office()
        jobs = task.create_geocoding_jobs()
        self.assertEquals(len(jobs), 1)
        self.assertEquals(jobs[0][0], "1234")
        self.assertEquals(jobs[0][1], "30 rue Edouard Poisson 93300 AUBERVILLIERS")

    def test_update_coordinates(self):
        make_geocoded_office()
        task = GeocodeJob()
        updates = [["1234", [0, 43]]]
        task.update_coordinates(updates)
        office = Office.query.first()
        self.assertEquals(int(office.x), 0)
        self.assertEquals(int(office.y), 43)
