import sys

from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.importer.util import parse_dpae_line
from .common import logger


def get_n_lines(path, n=5, ignore_header=True):
    results = []
    count = 0
    with import_util.get_reader(path) as myfile:
        if ignore_header:
            myfile.readline().strip()
        for line in myfile:
            results.append(line)
            count += 1
            if count >= n:
                break
    return results


def check_smoke_test(dpae_filename):
    logger.info("check smoke test...")
    lines = get_n_lines(dpae_filename, n=3)
    for line in lines:
        logger.info("sample line: %r", line)
        parse_dpae_line(line)

    logger.info("smoke test OK!")


def check_complete_test(dpae_filename):
    logger.info("check complete test...")
    lines = get_n_lines(dpae_filename, n=20)
    success = 0
    errors = 0
    for line in lines:
        try:
            parse_dpae_line(line)
            success += 1
        except (ValueError, IndexError):
            errors += 1
    logger.info("%i lines parsed with success", success)
    logger.info("%i lines parsed with error", errors)
    error_rate = errors / (1.0 * (success + errors))
    logger.info("error rate: %i", error_rate)
    if error_rate >= settings.DPAE_ERROR_RATE_MAX:
        raise "error_rate too high"
    logger.info("complete test OK!")


def check_file(dpae_filename):
    logger.info("going to check file %s", dpae_filename)
    check_smoke_test(dpae_filename)
    check_complete_test(dpae_filename)
    logger.info("all tests passed with flying colors!")


if __name__ == "__main__":
    filename = import_util.detect_runnable_file("dpae")
    if filename:
        check_file(filename)
        with open(import_util.JENKINS_DPAE_PROPERTIES_FILENAME, "w") as f:
            f.write("LBB_DPAE_INPUT_FILE=%s\n" % filename)
        sys.exit(0)
    else:
        sys.exit(-1)
