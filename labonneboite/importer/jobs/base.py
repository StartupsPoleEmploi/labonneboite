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
        if settings.BACKUP_FIRST:
            logger.info("backing up existing table before proceeding...")
            self.back_up_input_table()
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
        if not self.input_filename in files:
            raise "file does not exist"
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

    @timeit
    def back_up_input_table(self):
        timestamp = datetime.now().strftime('%Y_%m_%d_%H%M')
        import_util.back_up(settings.BACKUP_INPUT_FOLDER, self.table_name, self.file_type, timestamp)
