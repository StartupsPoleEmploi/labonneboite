# coding: utf8
import datetime

from sqlalchemy import Column, Index, Integer, BigInteger, String, Float, DateTime
from sqlalchemy import PrimaryKeyConstraint

from labonneboite.importer import settings as importer_settings
from labonneboite.common.database import Base
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common.models import PrimitiveOfficeMixin, FinalOfficeMixin


class Dpae(CRUDMixin, Base):
    """
    DPAE = Déclaration préalable à l'embauche.
    Each entry details a single hiring of a single office.
    """
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
    Initial large table storing all 10M offices and acting as the 'input' of the importer jobs.
    Stores the totality of officially existing offices at the time.
    About 10M sirets are indeed officially registered in France.
    """
    __tablename__ = importer_settings.RAW_OFFICE_TABLE
    __table_args__ = (
        Index('dept_i', 'departement'),
        PrimaryKeyConstraint('siret'),
    )

    # columns specific to this very model
    website1 = Column(String(191))
    website2 = Column(String(191))


class ExportableOffice(FinalOfficeMixin, CRUDMixin, Base):
    """
    Final output table of the importer jobs, typically storing only 500K offices
    which are selected by the importers jobs as having the highest hiring
    potential amongst all existing 10M offices stored in the raw office table.

    This model is exactly similar to the main Office model, the only difference
    is that they are stored in two different tables.

    When a new dataset built by the importer is deployed, the content of this
    table will replace the content of the main Office table.
    """
    __tablename__ = importer_settings.SCORE_REDUCING_TARGET_TABLE
    __table_args__ = (
        Index('dept_i', 'departement'),
        PrimaryKeyConstraint('siret'),
    )


class Geolocation(CRUDMixin, Base):
    """
    cache each full_address <=> coordinates(longitude, latitude) match
    managed by geocoding process
    """
    __tablename__ = "geolocations"
    full_address = Column(String(191), primary_key=True)
    x = Column('coordinates_x', Float)  # longitude
    y = Column('coordinates_y', Float)  # latitude


class ImportTask(CRUDMixin, Base):
    """
    Used to store and remember which ETAB and/or DPAE exports have already been processed
    by the importer jobs.
    """
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
    """
    Used to store details about the last DPAE import.
    """
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
