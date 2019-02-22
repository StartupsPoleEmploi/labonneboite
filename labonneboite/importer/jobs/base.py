"""

Every child class of this Job class is launchable via a jenkins job on the computing server.

"""


import os
from datetime import datetime
import logging
from labonneboite.importer import settings
from labonneboite.importer import util as import_util
from labonneboite.common.util import timeit
from labonneboite.importer.models.computing import ImportTask

logger = logging.getLogger('main')


class Job(object):
    file_type = None
    table_name = None
    import_type = None
    input_filename = None

    @timeit
    def run(self):
        if self.file_type:
            logger.info("file type:%s, checking the task is runnable with that file", self.file_type)
            self.check_runnable()
        if self.import_type:
            logger.info("recording in db we processed this input file...")
            self.record_task()
        logger.info("let's run this task!")
        self.run_task()
        self.after_check()
        logger.info("task is done.")

    def check_runnable(self):
        files = [
            os.path.join(os.path.normpath(settings.INPUT_SOURCE_FOLDER), name)
                for name in os.listdir(settings.INPUT_SOURCE_FOLDER)
        ]
        # We only compare realpath here, to solve a bug met in jenkins environment only.
        # In jenkins environment:
        # /srv/lbb is a symlink to /srv/jenkins/workspace/lbb
        # so that /srv/lbb/labonneboite path is the same on both local test and jenkins test.
        # However here,
        # self.input_filename == /srv/jenkins/workspace/lbb/labonneboite/importer/tests/data/...
        # but files are like /srv/lbb/labonneboite/importer/tests/data/...
        # hence why we use realpath here.
        if not os.path.realpath(self.input_filename) in [os.path.realpath(f) for f in files]:
            msg = "File %s does not exist: not found in list %s" % (
                self.input_filename, ','.join(files))
            raise IOError(msg)
        if import_util.is_processed(self.input_filename):
            raise "fatal error : cannot run task %s which is already marked as processed" % self.input_filename

    def after_check(self):
        pass

    def record_task(self):
        task = ImportTask(
            filename=os.path.basename(self.input_filename),
            state=ImportTask.FILE_READ,
            import_type=self.import_type,
        )
        task.save()
