import os
import datetime

from .test_base import DatabaseTest
from labonneboite.importer.jobs.performance_insert_data import (get_available_files_list,
                                                                insert_into_sql_table_old_prediction_file,
                                                                insert_data,
                                                                compute_effective_and_predicted_hirings)
from labonneboite.importer.models.computing import PerfImporterCycleInfos, PerfPredictionAndEffectiveHirings
from labonneboite.importer import util as import_util


def make_fake_perf_importer_cycles_infos_id():
    cycle_infos = PerfImporterCycleInfos(
        execution_date=datetime.datetime.now(),
        prediction_start_date=datetime.datetime.now(),
        prediction_end_date=datetime.datetime.now(),
        file_name="dummy_export_etablissement_backup_2020_11_12_1746.sql.gz",
        computed=False,
        on_google_sheets=False
    )
    cycle_infos.save()


class TestPerfInsertData(DatabaseTest):

    def test_get_available_files_list(self):
        make_fake_perf_importer_cycles_infos_id()
        files_list = get_available_files_list(path_folder=os.path.join(os.path.dirname(__file__),
                                                                       "data"))
        self.assertTrue(len(files_list) == 1)
        self.assertTrue("export_etablissement_backup_2019_11_10_1716.sql.gz" in files_list[0])

    def test_insert_data_from_file(self):
        file = get_available_files_list(path_folder=os.path.join(os.path.dirname(__file__),
                                                                       "data"))[0]
        insert_into_sql_table_old_prediction_file(file)
        insert_data(file, months_time=4)
        con, cur = import_util.create_cursor()
        cur.execute("select count(*) from etablissements_new;")
        number_new_offices = cur.fetchone()[0]
        self.assertTrue(number_new_offices == 2)
        self.assertTrue(
            PerfImporterCycleInfos.query.filter(
                PerfImporterCycleInfos.file_name==file).count() == 1)

    def test_compute_data(self):
        compute_effective_and_predicted_hirings()
        fields_not_null = ["lbb_nb_predicted_hirings",
                           "lba_nb_predicted_hirings",
                           "lbb_nb_effective_hirings",
                           "lba_nb_effective_hirings",
                           "is_a_bonne_boite",
                           "is_a_bonne_alternance"]
        for ppaeh in PerfPredictionAndEffectiveHirings.query.all():
            for field in fields_not_null:
                self.assertTrue(getattr(ppaeh, field) is not None)
