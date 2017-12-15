import os

# Environment
# -----------

ENV_DEVELOPMENT = 'development'
ENV_PRODUCTION = 'production'
ENV_STAGING = 'staging'
ENV_TEST = 'test'
ENV_LBBDEV = 'lbbdev'

ENVS = [ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_STAGING, ENV_TEST, ENV_LBBDEV]


def get_current_env():
    current_env = os.getenv('LBB_ENV')
    if not current_env or current_env not in ENVS:
        raise Exception(
            "To identify the current environment, an `LBB_ENV` environment variable must be set "
            "with one of those values: %s." % ', '.join(ENVS)
        )
    return current_env
