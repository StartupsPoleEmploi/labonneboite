import sys
from labonneboite.importer import util as import_util

def run():
    filename = import_util.detect_runnable_file("etablissements")
    if filename:
        sys.exit(0)
    else:
        sys.exit(-1)

if __name__ == '__main__':
    run()
