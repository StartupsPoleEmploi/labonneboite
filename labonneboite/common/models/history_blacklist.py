from sqlalchemy import Column
from sqlalchemy import BigInteger, String, DateTime
from labonneboite.common.database import Base
from labonneboite.common.models.base import CRUDMixin


class HistoryBlacklist(CRUDMixin, Base):
    __tablename__ = 'history_blacklist'

    id = Column("id", BigInteger, primary_key=True)
    email = Column(String(191), default='', nullable=False)
    datetime_removal = Column("datetime_removal", DateTime, nullable=False)
