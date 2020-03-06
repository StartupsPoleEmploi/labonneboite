from labonneboite.conf import settings

def get_api_user_data(user, default):
    return settings.API_KEYS.get(user, default)

def get_api_user_scopes(user, default=None):
    result = get_api_user_data(user, {'scopes': default} if default else None)
    return result.get('scopes') if result is not None else default

def get_api_user_key(user, default=None):
    result = get_api_user_data(user, {'key': default} if default else None)
    return result.get('key') if result is not None else default

