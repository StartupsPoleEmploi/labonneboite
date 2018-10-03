import imp
import os

from labonneboite.conf.common import settings_common

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
    
    settings_module = os.path.join(os.path.dirname(__file__), 'local_settings.py')
    settings_module = os.environ.get('LBB_SETTINGS', settings_module)
    try:
        settings = imp.load_source('settings', settings_module)
    except FileNotFoundError:
        pass
    else:
        # Iterate over each setting defined in the `settings_common` module and add them to the dynamically
        # imported `settings` module if they don't already exist.
        for setting in dir(settings_common):
            if not hasattr(settings, setting):
                setattr(settings, setting, getattr(settings_common, setting))
