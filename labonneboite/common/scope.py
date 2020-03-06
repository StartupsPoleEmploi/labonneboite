from enum import auto, Enum

class Scope(Enum):
    COMPANY_EMAIL = auto()
    COMPANY_PHONE = auto()
    COMPANY_WEBSITE = auto()
    COMPANY_POE = auto()
    COMPANY_PMSMP = auto()

SCOPES_ALL = [Scope.COMPANY_EMAIL, Scope.COMPANY_PHONE, Scope.COMPANY_WEBSITE, Scope.COMPANY_POE, Scope.COMPANY_PMSMP]
SCOPES_SAFE = [Scope.COMPANY_WEBSITE, Scope.COMPANY_PMSMP]
