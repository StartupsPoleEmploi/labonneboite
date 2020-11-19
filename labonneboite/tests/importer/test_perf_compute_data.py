from labonneboite.importer.jobs.performance_compute_data import (lancement_requete,
                                                                 PayloadDataframe,prepare_google_sheet_data)
from labonneboite.importer.models.computing import PerfImporterCycleInfos, PerfDivisionPerRome, PerfPredictionAndEffectiveHirings
from .test_base import DatabaseTest
from labonneboite.common import load_data
from datetime import datetime

result_df_global = {'cycle': [1, 2, 3],
                    'nbTotal': [2, 10, 4],
                    'sum10': [0.0, 0.4076086956521739, 0.0],
                    'sum20': [0.0, 0.8152173913043478, 0.0],
                    'sum30': [0.0, 0.90625, 0.48936170212765956],
                    'sum40': [0.0, 0.9375, 0.48936170212765956],
                    'sum50': [1.0, 0.96875, 0.9787234042553191],
                    'sum60': [1.0, 0.9959239130434783, 0.9787234042553191],
                    'sum70': [1.0, 0.9972826086956522, 0.9787234042553191],
                    'sum80': [1.0, 0.998641304347826, 1.0],
                    'sum90': [1.0, 1.0, 1.0],
                    'RMSE': [212.13203435596427, 98.54947995803936, 31.12876483254676],
                    'nbTotalLBX': [2, 8, 4],
                    'propRecrutNonLBX': [0.0, 0.2, 0.0]
                    }

result_df_naf = {'cycle': [1, 1, 2, 2, 2, 3, 3, 3, 3],
                 'naf': ['1091Z', '4920Z', '1089Z', '4920Z', '8130Z', '1089Z', '1091Z', '4920Z', '8130Z'],
                 'nbTotal': [1, 1, 2, 2, 5, 1, 1, 1, 1],
                 'sum10': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                 'sum20': [0.0, 0.0, 0.0, 0.0, 0.7204301075268817, 0.0, 0.0, 0.0, 0.0],
                 'sum30': [0.0, 0.0, 0.0, 0.0, 0.7204301075268817, 0.0, 0.0, 0.0, 0.0],
                 'sum40': [0.0, 0.0, 0.0, 0.0, 0.967741935483871, 0.0, 0.0, 0.0, 0.0],
                 'sum50': [0.0, 0.0, 1.0, 0.9287925696594427, 0.967741935483871, 0.0, 0.0, 0.0, 0.0],
                 'sum60': [0.0, 0.0, 1.0, 0.9287925696594427, 0.978494623655914, 0.0, 0.0, 0.0, 0.0],
                 'sum70': [0.0, 0.0, 1.0, 0.9287925696594427, 0.978494623655914, 0.0, 0.0, 0.0, 0.0],
                 'sum80': [0.0, 0.0, 1.0, 0.9287925696594427, 0.989247311827957, 0.0, 0.0, 0.0, 0.0],
                 'sum90': [0.0, 0.0, 1.0, 0.9287925696594427, 0.989247311827957, 0.0, 0.0, 0.0, 0.0],
                 'RMSE': [300.0, 0.0, 212.13203435596427, 31.11269837220809, 31.887301547794852, 2.0, 0.0, 44.0, 44.0],
                 'nbTotalLBX': [1, 1, 2, 2, 4, 1, 1, 1, 1],
                 'propRecrutNonLBX': [0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0]
                 }

result_df_dep = {'cycle': [1, 2, 2, 2, 3, 3],
                 'dep': ['44', '13', '44', '75', '44', '49'],
                 'nbTotal': [2, 2, 6, 2, 3, 1],
                 'sum10': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                 'sum20': [0.0, 0.0, 0.5775862068965517, 0.0, 0.0, 0.0],
                 'sum30': [0.0, 0.0, 0.5775862068965517, 0.0, 0.0, 0.0],
                 'sum40': [0.0, 0.0, 0.7758620689655172, 0.0, 0.9583333333333334, 0.0],
                 'sum50': [1.0, 0.9375, 0.9741379310344828, 1.0, 0.9583333333333334, 0.0],
                 'sum60': [1.0, 0.9375, 0.9741379310344828, 1.0, 0.9583333333333334, 0.0],
                 'sum70': [1.0, 0.9375, 0.9827586206896551, 1.0, 1.0, 0.0],
                 'sum80': [1.0, 0.9375, 0.9827586206896551, 1.0, 1.0, 0.0],
                 'sum90': [1.0, 0.9375, 0.9913793103448276, 1.0, 1.0, 0.0],
                 'RMSE': [212.13203435596427, 7.0710678118654755, 34.20526275297414, 212.13203435596427, 25.4296414970142, 44.0],
                 'nbTotalLBX': [2, 1, 5, 2, 3, 1],
                 'propRecrutNonLBX': [0.0, 0.5, 0.16666666666666666, 0.0, 0.0, 0.0]
                 }


def load_csv_perf_division_per_rome(filename, delimiter=';'):

    for row in load_data.load_csv_file(filename, delimiter):
        perf_div_per_rome = PerfDivisionPerRome(
            _id=row[0],
            importer_cycle_infos_id=row[1],
            naf=row[3],
            rome=row[2],
            threshold_lbb=row[4],
            nb_bonne_boites_lbb=row[5],
            threshold_lba=row[6],
            nb_bonne_boites_lba=row[7]
        )
        perf_div_per_rome.save()


def load_csv_perf_importer_cycle_infos(filename, delimiter=';'):
    for row in load_data.load_csv_file(filename, delimiter):
        perf_importer_cycle_info = PerfImporterCycleInfos(
            _id=row[0],
            execution_date=datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f'),
            prediction_start_date=datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S.%f'),
            prediction_end_date=datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f'),
            file_name=row[4],
            computed=(row[5] == 'True'),
            on_google_sheets=(row[6] == 'True')
        )
        perf_importer_cycle_info.save()


def load_csv_perf_prediction_and_effective_h(filename, delimiter=';'):
    for row in load_data.load_csv_file(filename, delimiter):
        perf_importer_cycle_info = PerfPredictionAndEffectiveHirings(
            _id=row[0],
            importer_cycle_infos_id=row[1],
            siret=row[2],
            naf=row[3],
            city_code=row[4],
            zipcode=row[5],
            departement=row[6],
            company_name=row[7],
            office_name=row[8],
            lbb_nb_predicted_hirings_score=row[9],
            lba_nb_predicted_hirings_score=row[10],
            lbb_nb_predicted_hirings=row[11],
            lba_nb_predicted_hirings=row[12],
            lbb_nb_effective_hirings=row[13],
            lba_nb_effective_hirings=row[14],
            is_a_bonne_boite=(row[15] == "True"),
            is_a_bonne_alternance=(row[16] == "True")
        )
        perf_importer_cycle_info.save()


def load_data_set_up():
    load_csv_perf_importer_cycle_infos("../../tests/importer/data/perf_importer_cycle_infos.csv")
    load_csv_perf_division_per_rome("../../tests/importer/data/perf_division_per_rome.csv")
    load_csv_perf_prediction_and_effective_h("../../tests/importer/data/perf_prediction_and_effective_h.csv")


class TestPerfComputeData(DatabaseTest):

    def test_lancement_requete(self):
        load_data_set_up()
        pdf = PayloadDataframe()
        df_naf = lancement_requete(pdf, "codenaf", "naf", is_lbb=True)
        df_dep = lancement_requete(pdf, "departement", "dep", is_lbb=True)
        df_global = lancement_requete(pdf, "global", is_lbb=True)
        for df, results in [(df_naf,result_df_naf), (df_dep, result_df_dep), (df_global, result_df_global)]:
            for column in results.keys():
                self.assertTrue(results[column] == df[column].tolist())
