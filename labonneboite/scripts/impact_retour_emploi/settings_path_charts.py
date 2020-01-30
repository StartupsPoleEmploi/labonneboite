from labonneboite.importer import settings as importer_settings

root_path = importer_settings.INPUT_SOURCE_FOLDER + '/impact_retour_emploi/'
images_path = root_path + 'images/'
gd_pub_path = root_path + 'gd_pub/'
clean_path = root_path + 'Clean/'

DEBUG = False
JOIN_ON_SIREN = False  # If False, we join on SIRET

SPREADSHEET_ID = '1kx-mxCaXIkys3hU4El4K7a6JBwzrdF75X4U8igqLB4I'
# SPREADSHEET_ID = '1cUfc1Nr9QSxA71HKpxMVhora-TqP8-aOVqpWriOwlpU'

ORDERING_COLUMN = ['date_begin', 'date_end', 'count_distinct_idpe',
                   'count_distinct_activity', 'count_postule', 'count_dpae_lbb', 'tre_min', 'tre_max']
