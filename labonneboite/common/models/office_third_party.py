import re
import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy import Column, ForeignKey
from sqlalchemy import desc
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import mysql

from labonneboite.common.models.base import CRUDMixin
from labonneboite.common.database import Base
from labonneboite.common.models import OfficeAdminUpdate, OfficeUpdateMixin

class OfficeThirdPartyUpdate(OfficeUpdateMixin, CRUDMixin, Base):

    __tablename__ = 'etablissements_third_party_update'
    id = Column(Integer, primary_key=True)

