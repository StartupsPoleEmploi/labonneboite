import imp
import os
import logging
from labonneboite.common.conf.common import settings_common


# Settings
# --------

# Default settings of the application are defined in `labonneboite/conf/common/settings_common.py`.
# A specific environment (staging, production...) can define its custom settings by:
# - creating a specific `settings` file, e.g. `lbb_staging_settings.py`
# - defining an environment variable containing the path to this specific `settings` file
#
# Specific and default settings will be merged, and values found in specific settings will take precedence.
# When no specific settings are found, `labonneboite/conf/local_settings.py` is used.

# Dynamically import LBB_SETTINGS environment variable as the `settings`
# module, or import `local_settings.py` as the `settings` module if it does not
# exist.

settings = settings_common

# Don't override settings in tests
if settings_common.get_current_env() != settings_common.ENV_TEST:

    if 'LBB_SETTINGS' not in os.environ:
        raise Exception('LBB_SETTINGS environment variable is required')

    settings_module: str = os.environ.get('LBB_SETTINGS')

    if os.path.exists(settings_module):

        settings = imp.load_source('settings', settings_module)

        for setting in dir(settings_common):

            if not hasattr(settings, setting):
                print(f"Setting {setting} not found. Using default.")
                setattr(settings, setting, getattr(settings_common, setting))
    else:
        # we don't want to block the docker build, so this should only be a warning
        print(
            f"Could not find configuration file LBB_SETTINGS : {settings_module}. Check your file path! It will be ignored!")
