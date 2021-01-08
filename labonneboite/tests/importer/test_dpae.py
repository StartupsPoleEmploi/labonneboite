from labonneboite.importer.jobs import check_dpae
from labonneboite.importer.jobs import extract_dpae
from labonneboite.importer.models.computing import Hiring
from labonneboite.importer.util import get_departement_from_zipcode
from .test_base import DatabaseTest

FIRST_DPAE_FILE_NAME = "lbb_xdpdpae_delta_201611102200.csv"
SECOND_DPAE_FILE_NAME = "lbb_xdpdpae_delta_201612102200.csv"

class TestDpae(DatabaseTest):

    def test_check_dpae(self):
        filename = self.get_data_file_path(FIRST_DPAE_FILE_NAME)
        check_dpae.check_file(filename)
        self.assertEqual(Hiring.query.count(), 0)

    def test_extract_dpae(self):
        self.assertEqual(Hiring.query.count(), 0)
        filename = self.get_data_file_path(FIRST_DPAE_FILE_NAME)
        task = extract_dpae.DpaeExtractJob(filename)
        task.run()
        self.assertEqual(Hiring.query.count(), 6)

    def test_extract_dpae_two_files_diff(self):
        # Second file contains one record from the future
        filename_first_month = self.get_data_file_path(FIRST_DPAE_FILE_NAME)
        filename_second_month = self.get_data_file_path(SECOND_DPAE_FILE_NAME)
        task = extract_dpae.DpaeExtractJob(filename_first_month)
        task.run()
        self.assertEqual(Hiring.query.count(), 6)
        task = extract_dpae.DpaeExtractJob(filename_second_month)
        task.run()
        # change 6+5 to 6+2, only 2 dpae is between 10/11/2016 and 10/12/2016 in SECOND_DPAE_FILE_NAME
        self.assertEqual(Hiring.query.count(), 6+2)

    def test_extract_departement(self):
        departement = get_departement_from_zipcode("6600")
        self.assertEqual(departement, "06")

    def test_extract_gz_format(self):
        filename = self.get_data_file_path(FIRST_DPAE_FILE_NAME + ".gz")
        task = extract_dpae.DpaeExtractJob(filename)
        task.run()
        self.assertEqual(Hiring.query.count(), 6)

    def test_extract_bz2_format(self):
        filename = self.get_data_file_path(FIRST_DPAE_FILE_NAME + ".bz2")
        task = extract_dpae.DpaeExtractJob(filename)
        task.run()
        self.assertEqual(Hiring.query.count(), 6)
