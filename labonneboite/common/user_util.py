from labonneboite.conf import settings

from enum import auto, Enum

class UnknownUserException(Exception):
    pass

class Gender(Enum):
  MALE = 'male'
  FEMALE = 'female'
  OTHER = 'autre'

def has_scope(user_name, scope):
    user_data = settings.API_KEYS.get(user_name)
    if(user_data is None):
        return False
    return scope in user_data.get('scopes')

def get_key(user_name, default = None):
    return settings.API_KEYS.get(user_name, {'key': default}).get('key')

def string_to_enum(EnumClass, value, default = None):
    '''
    Get an enum member out of a string value, e.g. Color.BLUE out of 'blue'
    Used to convert value in GET to enum
    TODO: find a better package for this method which is not user related
    '''
    for enumMember in EnumClass:
          if(enumMember.value == value):
              return enumMember
    return default
