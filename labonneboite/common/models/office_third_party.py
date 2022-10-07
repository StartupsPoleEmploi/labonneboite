from sqlalchemy import Integer
from sqlalchemy import Column
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common.database import Base
from labonneboite.common.models import OfficeAdminUpdate, OfficeUpdateMixin  # noqa


class OfficeThirdPartyUpdate(OfficeUpdateMixin, CRUDMixin, Base):

    __tablename__ = 'etablissements_third_party_update'
    id = Column(Integer, primary_key=True)
