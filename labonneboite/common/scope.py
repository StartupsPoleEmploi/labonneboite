'''
    This file is imported in settings, so it can not import settings
    It is meant to hold constants for scopes
    @see user.py for methods using scopes
'''

from enum import auto, Enum

class Scope(Enum):
    COMPANY_EMAIL = auto()
    COMPANY_PHONE = auto()
    COMPANY_WEBSITE = auto()
    COMPANY_BOE = auto()
    COMPANY_PMSMP = auto()

SCOPES_SAFE = [Scope.COMPANY_WEBSITE]
SCOPES_INTERNAL = SCOPES_SAFE + [Scope.COMPANY_EMAIL, Scope.COMPANY_PHONE]
