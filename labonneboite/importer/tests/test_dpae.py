from labonneboite.importer.jobs import check_dpae
from labonneboite.importer.jobs import extract_dpae
from labonneboite.importer.models.computing import Dpae
from labonneboite.importer.tests.test_base import DatabaseTest
from labonneboite.importer.util import extract_departement_from_zipcode


class TestDpae(DatabaseTest):

    def test_check_dpae(self):
        filename = self.get_data_file_path("LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv")
        check_dpae.check_file(filename)
        self.assertEquals(Dpae.query.count(), 0)

    def test_extract_dpae(self):
        filename = self.get_data_file_path("LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv")
        extract_dpae.DpaeExtractJob.backup_first = False
        task = extract_dpae.DpaeExtractJob(filename)
        task.run()
        self.assertEquals(Dpae.query.count(), 6)

    def test_extract_dpae_two_files_diff(self):
        # Updated file contains duplicated records and one record from the future and only 2 really new valid records.
        filename_first_month = self.get_data_file_path("LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv")
        filename_second_month = self.get_data_file_path("LBB_XDPDPA_DPAE_20151110_20161210_20161210_094110.csv")
        extract_dpae.DpaeExtractJob.backup_first = False
        task = extract_dpae.DpaeExtractJob(filename_first_month)
        task.run()
        self.assertEquals(Dpae.query.count(), 6)
        task = extract_dpae.DpaeExtractJob(filename_second_month)
        task.run()
        self.assertEquals(Dpae.query.count(), 6+2)

    def test_extract_departement(self):
        departement = extract_departement_from_zipcode("6600", None)
        self.assertEqual(departement, "06")

    def test_extract_gz_format(self):
        filename = self.get_data_file_path("LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv.gz")
        extract_dpae.DpaeExtractJob.backup_first = False
        task = extract_dpae.DpaeExtractJob(filename)
        task.run()
        self.assertEquals(Dpae.query.count(), 6)

    def test_extract_bz2_format(self):
        filename = self.get_data_file_path("LBB_XDPDPA_DPAE_20151010_20161110_20161110_174915.csv.bz2")
        extract_dpae.DpaeExtractJob.backup_first = False
        task = extract_dpae.DpaeExtractJob(filename)
        task.run()
        self.assertEquals(Dpae.query.count(), 6)
