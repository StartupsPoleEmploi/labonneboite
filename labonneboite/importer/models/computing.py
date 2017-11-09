# coding: utf8
import datetime

from sqlalchemy import Column, Index, Integer, BigInteger, String, Float, DateTime
from sqlalchemy import PrimaryKeyConstraint

from labonneboite.importer import settings as importer_settings
from labonneboite.common.database import Base
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common.models import PrimitiveOfficeMixin

class Dpae(CRUDMixin, Base):
    __tablename__ = importer_settings.DPAE_TABLE

    _id = Column('id', BigInteger, primary_key=True)
    siret = Column(String(191))
    hiring_date = Column(DateTime, default=datetime.datetime.utcnow)
    zipcode = Column(String(8))
    contract_type = Column(Integer)
    departement = Column(String(8))
    contract_duration = Column(Integer)
    iiann = Column(String(191))
    age_group = Column('tranche_age', String(191))
    handicap_label = Column(String(191))

    def __str__(self):
        return '%s %s' % (self.siret, self.hiring_date)


class RawOffice(PrimitiveOfficeMixin, CRUDMixin, Base):
    """
    raw importer table storing all 10M offices
    FIXME DNRY mixin
    """
    __tablename__ = importer_settings.OFFICE_TABLE
    __table_args__ = (
        Index('dept_i', 'departement'),
        PrimaryKeyConstraint('siret'),
    )
    #     siret = Column(String(14), primary_key=True)

    # begin specific
    website1 = Column(String(191))
    website2 = Column(String(191))
    # end specific


class Geolocation(CRUDMixin, Base):
    """
    cache each full_address <=> coordinates(longitude, latitude) match
    managed by geocoding process
    """
    __tablename__ = "geolocations"
    full_address = Column(String(191), primary_key=True)
    x = Column('coordinates_x', Float)  # longitude
    y = Column('coordinates_y', Float)  # latitude


# FIXME DNRY mixin
# class ExportableOffice(CRUDMixin, Base):
#     """
#     importer table including selected offices (~500K)
#     ready to be exported to staging and production
#     -
#     note that this is actually a duplicate of the Office model
#     in common/models/office.py
#     FIXME fix duplication of office model between app and importer
#     """
#     __tablename__ = 'etablissements'
#     siret = Column(String(14), primary_key=True)
#     company_name = Column('raisonsociale', String(191))
#     office_name = Column('enseigne', String(191))
#     naf = Column('codenaf', String(8))
#     street_number = Column('numerorue', String(191))
#     street_name = Column('libellerue', String(191))
#     city_code = Column('codecommune', String(191))
#     zipcode = Column('codepostal', String(8))
#     email = Column(String(191))
#     tel = Column(String(191))
#     website = Column(String(191))
#     flag_alternance = Column(Boolean, default=False, nullable=False)
#     flag_junior = Column(Boolean, default=False, nullable=False)
#     flag_senior = Column(Boolean, default=False, nullable=False)
#     flag_handicap = Column(Boolean, default=False, nullable=False)
#     has_multi_geolocations = Column(Boolean, default=False, nullable=False)

#     departement = Column(String(8))
#     headcount = Column('trancheeffectif', String(2))
#     score = Column(Integer)
#     x = Column('coordinates_x', Float)  # longitude
#     y = Column('coordinates_y', Float)  # latitude


class ImportTask(CRUDMixin, Base):
    __tablename__ = "import_tasks"

    # Import state
    FILE_READ = 1
    FILE_IMPORTED = 2
    NO_CHANGE = 3

    # Import type
    DPAE = 1
    ETABLISSEMENT = 2

    _id = Column('id', BigInteger, primary_key=True)
    filename = Column(String(191))
    state = Column(Integer)
    import_type = Column(Integer)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def is_last_import_dpae(cls):
        return cls.query.order_by(cls.created_date.desc()).first().import_type == ImportTask.DPAE


class DpaeStatistics(CRUDMixin, Base):
    __tablename__ = "dpae_statistics"

    _id = Column('id', BigInteger, primary_key=True)
    last_import = Column(DateTime, default=datetime.datetime.utcnow)
    most_recent_data_date = Column(DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def get_most_recent_data_date(cls):
        try:
            return cls.query.order_by(cls.most_recent_data_date.desc()).first().most_recent_data_date
        except AttributeError:
            # if there was no import of dpae thus far, return the date for which
            # we don't want to import dpae before that date
            return importer_settings.MOST_RECENT_DPAE_DATE
