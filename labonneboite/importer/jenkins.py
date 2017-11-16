import sys
from labonneboite.importer import settings
from labonneboite.conf import get_current_env, ENV_LBBDEV

def get_dpae_filename():
    if get_current_env() == ENV_LBBDEV:
        dpae_filename = sys.argv[1]
    else:
        with open(settings.JENKINS_DPAE_PROPERTIES_FILENAME, "r") as f:
            dpae_filename = f.read().strip().split('=')[1]
    return dpae_filename

def get_etablissement_filename():
    if get_current_env() == ENV_LBBDEV:
        etablissement_filename = sys.argv[1]
    else:
        with open(settings.JENKINS_ETAB_PROPERTIES_FILENAME, "r") as f:
            # file content looks like this:
            # LBB_ETABLISSEMENT_INPUT_FILE=/srv/lbb/labonneboite/importer/data/LBB_EGCEMP_ENTREPRISE_123.csv.bz2\n
            etablissement_filename = f.read().strip().split('=')[1]
    return etablissement_filename
