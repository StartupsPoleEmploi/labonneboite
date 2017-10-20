import sys
import os
from labonneboite.importer import util as import_util
from labonneboite.conf import get_current_env, ENV_LBBDEV
from .common import logger


if __name__ == "__main__":
    filename = import_util.detect_runnable_file("etablissements")
    if filename:
        if get_current_env() == ENV_LBBDEV:
            f = open(os.path.join(os.environ["WORKSPACE"], "properties.jenkins"), "w")
        else:  # local dev
            f = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../jenkins/properties.jenkins"), "w")
        f.write("LBB_ETABLISSEMENT_INPUT_FILE=%s\n" % filename)
        f.close()

        sys.exit(0)
    else:
        sys.exit(-1)
