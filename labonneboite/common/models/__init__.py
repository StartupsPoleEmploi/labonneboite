"""
Since model classes are stored in differents files and due to the behavior
of SQLAlchemy's "declarative" configuration mode, all modules which hold
active SQLAlchemy models need to be imported before those models can
successfully be used.

To solve this, we import them here, into models/__init__.py.
Then items can be imported accross the project as:
    `from labonneboite.common.models import User`

Without doing something like this, the different tables will not be attached
to the Base.

See:
- https://groups.google.com/forum/#!msg/pylons-discuss/tyRzeBjmak0/ORqjAqhmwwQJ
- https://stackoverflow.com/a/29219148

Warning: make sure the order of the imports matches the order of which the
dependent tables should be created.
"""
# pylint: disable=wildcard-import
from labonneboite.common.models.office_mixin import PrimitiveOfficeMixin, OfficeMixin, FinalOfficeMixin
from labonneboite.common.models.office_admin import OfficeAdminAdd, OfficeAdminRemove, OfficeUpdateMixin, \
    OfficeAdminUpdate, OfficeAdminExtraGeoLocation
from labonneboite.common.models.office_third_party import OfficeThirdPartyUpdate
from labonneboite.common.models.office import Office, OfficeResult
from labonneboite.common.models.auth import TokenRefreshFailure, User, get_user_social_auth
from labonneboite.common.models.user_favorite_offices import UserFavoriteOffice
from labonneboite.common.models.recruiter_message import NoOfficeFoundException, RecruiterMessageCommon, \
    OtherRecruiterMessage, RemoveRecruiterMessage, UpdateCoordinatesRecruiterMessage, UpdateJobsRecruiterMessage
from labonneboite.common.models.history_blacklist import HistoryBlacklist

# pylint: enable=wildcard-import

__all__ = [
    "PrimitiveOfficeMixin", "OfficeMixin", "FinalOfficeMixin",
    "OfficeAdminAdd", "OfficeAdminRemove", "OfficeUpdateMixin", "OfficeAdminUpdate", "OfficeAdminExtraGeoLocation",
    "OfficeThirdPartyUpdate",
    "Office", "OfficeResult",
    "TokenRefreshFailure", "User", "get_user_social_auth",
    "UserFavoriteOffice",
    "NoOfficeFoundException", "RecruiterMessageCommon", "OtherRecruiterMessage", "RemoveRecruiterMessage",
    "UpdateCoordinatesRecruiterMessage", "UpdateJobsRecruiterMessage",
    "HistoryBlacklist",
]
