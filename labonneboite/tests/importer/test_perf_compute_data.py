from labonneboite.importer.jobs.performance_compute_data import (lancement_requete,
                                                                 PayloadDataframe,prepare_google_sheet_data)
from labonneboite.importer.models.computing import PerfImporterCycleInfos, PerfDivisionPerRome, PerfPredictionAndEffectiveHirings
from .test_base import DatabaseTest
from labonneboite.common import load_data
from datetime import datetime

result_df_global = {'cycle': [1, 2, 3],
                    'nbTotalHirings': [600.0, 1196.0, 137.0],
                    'nbTotal': [2, 10, 4],
                    'sum10': [0.0, 0.2508361204013378, 0.0],
                    'sum20': [0.0, 0.5016722408026756, 0.0],
                    'sum30': [0.0, 0.6045150501672241, 0.48905109489051096],
                    'sum40': [0.0, 0.6605351170568562, 0.48905109489051096],
                    'sum50': [0.5, 0.7165551839464883, 0.9781021897810219],
                    'sum60': [0.5, 0.7416387959866221, 0.9781021897810219],
                    'sum70': [0.5, 0.7441471571906354, 0.9781021897810219],
                    'sum80': [0.5, 0.7466555183946488, 1.0],
                    'sum90': [0.5, 0.7491638795986622, 1.0],
                    'RMSE': [212.13203435596427, 98.54947995803936, 31.12876483254676],
                    'nbTotalLBXHirings': [600.0, 1099.0, 137.0],
                    'nbTotalLBX': [2, 8, 4],
                    'propRecrutNonLBX': [0.0, 0.08110367892976589, 0.0]}


result_df_naf = {'cycle': [1, 1, 2, 2, 2, 3, 3, 3, 3],
                 'naf': ['1091Z', '4920Z', '1089Z', '4920Z', '8130Z', '1089Z', '1091Z', '4920Z', '8130Z'],
                 'nbTotalHirings': [300.0, 300.0, 600.0, 367.0, 199.0, 3.0, 0.0, 67.0, 67.0],
                 'nbTotal': [1, 1, 2, 2, 5, 1, 1, 1, 1],
                 'sum10': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                 'sum20': [0.0, 0.0, 0.0, 0.0, 0.6180904522613065, 0.0, 0.0, 0.0, 0.0],
                 'sum30': [0.0, 0.0, 0.0, 0.0, 0.6180904522613065, 0.0, 0.0, 0.0, 0.0],
                 'sum40': [0.0, 0.0, 0.0, 0.0, 0.9547738693467337, 0.0, 0.0, 0.0, 0.0],
                 'sum50': [0.0, 0.0, 0.5, 0.8174386920980926, 0.9547738693467337, 0.0, 0.0, 0.0, 0.0],
                 'sum60': [0.0, 0.0, 0.5, 0.8174386920980926, 0.9698492462311558, 0.0, 0.0, 0.0, 0.0],
                 'sum70': [0.0, 0.0, 0.5, 0.8174386920980926, 0.9698492462311558, 0.0, 0.0, 0.0, 0.0],
                 'sum80': [0.0, 0.0, 0.5, 0.8174386920980926, 0.9849246231155779, 0.0, 0.0, 0.0, 0.0],
                 'sum90': [0.0, 0.0, 0.5, 0.8174386920980926, 0.9849246231155779, 0.0, 0.0, 0.0, 0.0],
                 'RMSE': [300.0, 0.0, 212.13203435596427, 31.11269837220809, 31.887301547794852, 2.0, 0.0, 44.0, 44.0],
                 'nbTotalLBXHirings': [300.0, 300.0, 600.0, 367.0, 132.0, 3.0, 0.0, 67.0, 67.0],
                 'nbTotalLBX': [1, 1, 2, 2, 4, 1, 1, 1, 1],
                 'propRecrutNonLBX': [0.0, 0.0, 0.0, 0.0, 0.33668341708542715, 0.0, 1, 0.0, 0.0]}

result_df_dep = {'cycle': [1, 2, 2, 2, 3, 3],
                 'dep': ['44', '13', '44', '75', '44', '49'],
                 'nbTotalHirings': [600.0, 330.0, 266.0, 600.0, 70.0, 67.0],
                 'nbTotal': [2, 2, 6, 2, 3, 1],
                 'sum10': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                 'sum20': [0.0, 0.0, 0.462406015037594, 0.0, 0.0, 0.0],
                 'sum30': [0.0, 0.0, 0.462406015037594, 0.0, 0.0, 0.0],
                 'sum40': [0.0, 0.0, 0.7142857142857143, 0.0, 0.9571428571428572, 0.0],
                 'sum50': [0.5, 0.9090909090909091, 0.9661654135338346, 0.5, 0.9571428571428572, 0.0],
                 'sum60': [0.5, 0.9090909090909091, 0.9661654135338346, 0.5, 0.9571428571428572, 0.0],
                 'sum70': [0.5, 0.9090909090909091, 0.9774436090225563, 0.5, 1.0, 0.0],
                 'sum80': [0.5, 0.9090909090909091, 0.9774436090225563, 0.5, 1.0, 0.0],
                 'sum90': [0.5, 0.9090909090909091, 0.9887218045112782, 0.5, 1.0, 0.0],
                 'RMSE': [212.13203435596427, 7.0710678118654755, 34.20526275297414, 212.13203435596427, 25.4296414970142, 44.0],
                 'nbTotalLBXHirings': [600.0, 300.0, 199.0, 600.0, 70.0, 67.0],
                 'nbTotalLBX': [2, 1, 5, 2, 3, 1],
                 'propRecrutNonLBX': [0.0, 0.09090909090909091, 0.2518796992481203, 0.0, 0.0, 0.0]
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
        df_global = lancement_requete(pdf, "global", is_lbb=True)
        df_naf = lancement_requete(pdf, "codenaf", "naf", is_lbb=True)
        df_dep = lancement_requete(pdf, "departement", "dep", is_lbb=True)
        for df, results in [(df_naf,result_df_naf), (df_dep, result_df_dep), (df_global, result_df_global)]:
            for column in results.keys():
                self.assertTrue(results[column] == df[column].tolist())
