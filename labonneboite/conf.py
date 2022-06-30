import os

settings_module = os.path.join(os.path.dirname(__file__), 'conf', 'local_settings.py')
os.environ.setdefault('LBB_SETTINGS', settings_module)

from labonneboite.common import conf  # noqa: E402 = module level import not at top of file

settings = conf.settings
