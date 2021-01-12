import datetime

from sqlalchemy import Column, Index, Integer, BigInteger, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from labonneboite.importer import settings as importer_settings
from labonneboite.common.database import Base
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common.models import PrimitiveOfficeMixin, FinalOfficeMixin


class Hiring(CRUDMixin, Base):
    """
    Each entry details a single hiring of a single office.

    Various types of hirings are stored:
    
    DPAE : Déclaration préalable à l'embauche. (Pre-hiring declaration) has 3 subtypes:
    1) CDD  == Contrat à durée déterminée. (Fixed duration contract)
    2) CDI  == Contrat à durée indéterminée. (Regular contract)
    3) CTT  == Contrat de travail temporaire. (Seasonal contract) - never stored nor used (yet) in practise
    
    Alternance (another category of work contracts) has 2 subtypes:
    1) APR  == Apprentissage.
    2) CP   == Contrat professionnel.
    """
    __tablename__ = importer_settings.HIRING_TABLE
    __table_args__ = (
        # Improve performance of importer compute_scores parallel jobs
        # by quickly fetching all hirings of any given departement. 
        Index('_departement', 'departement'),

        # Make it fast to retrieve all hirings of a given siret.
        # For convenience only, not actually used by the importer itself.
        Index('_siret', 'siret'),
    )

    CONTRACT_TYPE_CDD = 1
    CONTRACT_TYPE_CDI = 2
    CONTRACT_TYPE_CTT = 3
    CONTRACT_TYPE_APR = 11
    CONTRACT_TYPE_CP = 12
    CONTRACT_TYPES_DPAE = [CONTRACT_TYPE_CDD, CONTRACT_TYPE_CDI, CONTRACT_TYPE_CTT]
    CONTRACT_TYPES_ALTERNANCE = [CONTRACT_TYPE_APR, CONTRACT_TYPE_CP]
    CONTRACT_TYPES_ALL = CONTRACT_TYPES_DPAE + CONTRACT_TYPES_ALTERNANCE

    _id = Column('id', BigInteger, primary_key=True)
    siret = Column(String(191))
    hiring_date = Column(DateTime, default=datetime.datetime.utcnow)
    contract_type = Column(Integer)
    departement = Column(String(8))
    contract_duration = Column(Integer)
    iiann = Column(String(191))
    age_group = Column('tranche_age', String(191))
    handicap_label = Column(String(191))
    duree_pec = Column(Integer, nullable=True)

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
        PrimaryKeyConstraint('siret'),
        
        # Improve performance of importer compute_scores parallel jobs
        # by quickly fetching all offices of any given departement.     
        Index('_departement', 'departement'),
    )

    # any column specific to this very model should go here.


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
        PrimaryKeyConstraint('siret'),

        # Improve performance of create_index.py parallel jobs
        # by quickly fetching all offices of any given departement.
        Index('_departement', 'departement'),
        
        # Improve performance of create_index.py remove_scam_emails()
        # by quickly locating offices having a given scam email.
        Index('_email', 'email'),
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
    APPRENTISSAGE = 3

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

    #File types
    DPAE = 1
    APR = 2
    PRO = 3

    _id = Column('id', BigInteger, primary_key=True)
    file_type = Column(Integer)
    last_import = Column(DateTime, default=datetime.datetime.utcnow)
    most_recent_data_date = Column(DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def get_last_historical_data_date(cls, file_type):
        try:
            return cls.query.order_by(cls.most_recent_data_date.desc()).filter_by(file_type=file_type).first().most_recent_data_date
        except AttributeError:
            # if there was no import of dpae thus far, return the date for which
            # we don't want to import dpae before that date
            return importer_settings.OLDEST_POSSIBLE_DPAE_DATE

# Tables needed for the "Impact sur le retour à l'emploi" project
#-------------------------------------
class LogsIDPEConnect(CRUDMixin, Base):
    """
    Used to store details about the idpeconnect which logged to lbb
    """
    __tablename__ = "logs_idpe_connect"

    _id = Column('id', BigInteger, primary_key=True)
    idutilisateur_peconnect = Column(Text)
    dateheure = Column(DateTime, default=datetime.datetime.utcnow)

class LogsActivity(CRUDMixin, Base):
    """
    Used to store details about the events on website LBB
    """
    __tablename__ = "logs_activity"

    _id = Column('id', BigInteger, primary_key=True)
    dateheure = Column(DateTime, default=datetime.datetime.utcnow)
    nom = Column(Text)
    idutilisateur_peconnect = Column(Text)
    siret = Column(Text)
    utm_medium = Column(Text)
    utm_source = Column(Text)
    utm_campaign = Column(Text)

class LogsActivityRecherche(CRUDMixin, Base):
    """
    Table which stores all queries made on the lbb website
    """
    __tablename__ = "logs_activity_recherche"

    _id = Column('id', BigInteger, primary_key=True)
    dateheure = Column(DateTime, default=datetime.datetime.utcnow)
    idutilisateur_peconnect = Column(Text)
    ville = Column(Text)
    code_postal = Column(Text)
    emploi = Column(Text)

class LogsActivityDPAEClean(CRUDMixin, Base):
    """
    Table which stores activity joined and dpae
    """
    __tablename__ = "logs_activity_dpae_clean"

    _id = Column('id', BigInteger, primary_key=True)
    idutilisateur_peconnect = Column(Text)
    siret = Column(Text)
    date_activite = Column(DateTime, default=None)
    date_embauche = Column(DateTime, default=None)
    type_contrat = Column(Text)
    duree_activite_cdd_mois = Column(Integer)
    duree_activite_cdd_jours = Column(Integer)
    diff_activite_embauche_jrs = Column(Integer)
    dc_lblprioritede = Column(Text)
    tranche_age = Column(Text)
    dc_prive_public = Column(Text)
    duree_prise_en_charge = Column(Integer)
    dn_tailleetablissement = Column(Integer)
    code_postal = Column(Text)


# FIXME : Replace with Enum if possible
StatusJobExecution = {
    'start' : 0,
    'done' : 1,
    'error' : 2
}


class HistoryImporterJobs(CRUDMixin, Base):
    """
    Used to store details about the running of the different importer jobs
    """
    __tablename__ = "history_importer_jobs"

    _id = Column('id', BigInteger, primary_key=True)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, default=None)
    job_name = Column(Text)
    status = Column(Integer)
    exception = Column(Text, default=None)
    trace_log = Column(Text, default=None)

    @classmethod
    def is_job_done(cls, job):
        most_recent_job_history = cls.query.filter_by(job_name=job).order_by(cls.start_date.desc()).first()

        #No rows matching to the job in the database
        if most_recent_job_history is None:
            return False

        # check if the most recent row in db for this job has start_date < 25 days
        # 25 days totally arbitrary, we run importer each month, and with this function, 
        # we want it to check the job status for the current importer cycle, not the previous one
        now = datetime.datetime.now()
        most_recent_start_date = most_recent_job_history.start_date
        delta = now - most_recent_start_date
        if delta.days > 25:
            return False

        return most_recent_job_history.status == StatusJobExecution['done']

## Tables needed for performance indicators
# -----------------------
class PerfImporterCycleInfos(CRUDMixin, Base):
    """
    Used to store details about the previous cycles of importer which have run (nb rows = NB_IMPORTER_CYCLES)
    """
    __tablename__ = "perf_importer_cycle_infos"

    _id = Column('id', BigInteger, primary_key=True)
    execution_date = Column(DateTime, default=None)
    prediction_start_date = Column(DateTime, default=None)
    prediction_end_date = Column(DateTime, default=None)
    file_name = Column(Text)
    computed = Column(Boolean)
    on_google_sheets = Column(Boolean)

class PerfPredictionAndEffectiveHirings(CRUDMixin, Base):
    """
    Used to compare effective (real) hirings in companies VS predicted hirings by importer algorithm (nb rows = NB_OFFICES * NB_IMPORTER_CYCLES)
    """
    __tablename__ = "perf_prediction_and_effective_hirings"

    _id = Column('id', BigInteger, primary_key=True)
    importer_cycle_infos_id = Column(BigInteger, ForeignKey('perf_importer_cycle_infos.id', ondelete='SET NULL'), nullable=True)
    siret = Column(String(191))
    naf = Column('codenaf', String(8))
    city_code = Column('codecommune', String(191))
    zipcode = Column('codepostal', String(8))
    departement = Column(String(8))
    company_name = Column('raisonsociale', String(191))
    office_name = Column('enseigne', String(191), default='')
    lbb_nb_predicted_hirings_score = Column(Integer) #Score associé au Nombre de recrutement prédits pour LBB (en utilisant les DPAE)
    lba_nb_predicted_hirings_score = Column(Integer) #Score associé au Nombre de recrutements prédits pour LBA (en utilisant APR et CP)
    lbb_nb_predicted_hirings = Column(Integer) #Nombre de recrutement prédits pour LBB (en utilisant les DPAE)
    lba_nb_predicted_hirings = Column(Integer) #Nombre de recrutements prédits pour LBA (en utilisant APR et CP)
    lbb_nb_effective_hirings = Column(Integer) #Nombre de recrutement effectifs pour LBB (en utilisant les DPAE)
    lba_nb_effective_hirings = Column(Integer) #Nombre de recrutements effectifs pour LBA (en utilisant APR et CP)
    is_a_bonne_boite = Column(Boolean) #Affiché ou non sur LBB (Dépasse pour au moins un rome le seuil) port_date = Column(DateTime, default=None)
    is_a_bonne_alternance = Column(Boolean) #Affiché ou non sur LBA (Dépasse pour au moins un rome le seuil) port_date = Column(DateTime, default=None)

class PerfDivisionPerRome(CRUDMixin, Base):
    """
    Used to check the repartition by rome code of the number of companies (nb rows = NB_DISTINCT_ROME_CODE * NB_IMPORTER_CYCLES)
    """
    __tablename__ = "perf_division_per_rome"

    _id = Column('id', BigInteger, primary_key=True)
    importer_cycle_infos_id = Column(BigInteger, ForeignKey('perf_importer_cycle_infos.id', ondelete='SET NULL'), nullable=True)
    naf = Column('codenaf', String(8), nullable=False)
    rome = Column('coderome', String(8), nullable=False)
    threshold_lbb = Column(Float)
    threshold_lba = Column(Float)
    nb_bonne_boites_lbb = Column(Integer)
    nb_bonne_boites_lba = Column(Integer)
