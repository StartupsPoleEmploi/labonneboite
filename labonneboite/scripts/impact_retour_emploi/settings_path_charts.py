from labonneboite.importer import settings as importer_settings

root_path = importer_settings.INPUT_SOURCE_FOLDER + '/impact_retour_emploi/'
images_path = root_path + 'images/'
gd_pub_path = root_path + 'gd_pub/'
clean_path = root_path +'Clean/'

DEBUG = True
JOIN_ON_SIREN = True # If False, we join on SIRET
