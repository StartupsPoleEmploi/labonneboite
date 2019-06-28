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
from labonneboite.common.models.office import *
from labonneboite.common.models.auth import *
from labonneboite.common.models.user_favorite_offices import *
from labonneboite.common.models.office_admin import *
from labonneboite.common.models.recruiter_message import *
# pylint: enable=wildcard-import
