# coding: utf8

from __future__ import division
import logging
from babel.dates import format_date

from slugify import slugify

from flask import url_for
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy import PrimaryKeyConstraint
from backports.functools_lru_cache import lru_cache

from labonneboite.common import encoding as encoding_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common import hiring_type_util
from labonneboite.common.database import Base, db_session, DATABASE
from labonneboite.common.load_data import load_city_codes
from labonneboite.common import util
from labonneboite.common.models.base import CRUDMixin
from labonneboite.conf import settings


logger = logging.getLogger('main')


CITY_NAMES = load_city_codes()


class PrimitiveOfficeMixin(object):
    """
    Mixin providing fields shared by models: RawOffice, ExportableOffice, Office, OfficeAdminAdd.

    Don't forget to create a new migration for each of these models
    each time you add/change/remove a field here to keep all models
    in sync.    """
    siret = Column(String(191))
    company_name = Column('raisonsociale', String(191), nullable=False)
    office_name = Column('enseigne', String(191), default='', nullable=False)
    naf = Column('codenaf', String(8), nullable=False)
    street_number = Column('numerorue', String(191), default='', nullable=False)
    street_name = Column('libellerue', String(191), default='', nullable=False)
    city_code = Column('codecommune', String(191), nullable=False)
    zipcode = Column('codepostal', String(8), nullable=False)
    email = Column(String(191), default='', nullable=False)
    tel = Column(String(191), default='', nullable=False)
    departement = Column(String(8), nullable=False)
    headcount = Column('trancheeffectif', String(2))


class OfficeMixin(PrimitiveOfficeMixin):
    """
    Mixin providing fields shared by models: ExportableOffice, Office, OfficeAdminAdd.

    Don't forget to create a new migration for each of these models
    each time you add/change/remove a field here to keep all models
    in sync.
    """
    website = Column(String(191), default='', nullable=False)
    email_alternance = Column('email_alternance', String(191), default='', nullable=True)
    flag_alternance = Column(Boolean, default=False, nullable=False)
    flag_junior = Column(Boolean, default=False, nullable=False)
    flag_senior = Column(Boolean, default=False, nullable=False)
    flag_handicap = Column(Boolean, default=False, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    score_alternance = Column(Integer, default=0, nullable=False)
    x = Column('coordinates_x', Float)  # Longitude.
    y = Column('coordinates_y', Float)  # Latitude.


class FinalOfficeMixin(OfficeMixin):
    """
    Mixin providing fields shared by models: ExportableOffice, Office.

    Don't forget to create a new migration for each of these models
    each time you add/change/remove a field here to keep all models
    in sync.
    """
    # A flag that is True if the office also recruits beyond the boundaries of its primary geolocation.
    has_multi_geolocations = Column(Boolean, default=False, nullable=False)


class Office(FinalOfficeMixin, CRUDMixin, Base):
    """
    An office.

    Warning: the table behind this model is regularly entirely dropped and recreated
    at the end of an importer cycle when a new dataset is deployed (once a month in theory).
    For this reason, it is very important that Office and ExportableOffice are kept 100% in
    sync, i.e. have the exact same columns.

    For example, if you want to add a new column, first be sure to give it a default value,
    as when the importer imports a new office dataset, this column will be entirely populated
    by this default value.

    Do *not* add this new column here in this model, but rather in the proper Mixin above,
    take time to read each Mixin role and choose the right one for your need.

    Then you need to add a migration to create this column in each relevant model,
    not just the Office model, see your Mixin documentation for the list of models.

    You also need to add this new column in these two files:
    labonneboite/importer/db/etablissements_exportable.sql
    labonneboite/importer/db/etablissements_backoffice.sql
    and in method importer.util.get_select_fields_for_main_db

    Then, be sure to double check that both `make run_importer_jobs` and
    `make test_all` complete successfully.
    """

    __tablename__ = settings.OFFICE_TABLE
    __table_args__ = (
        PrimaryKeyConstraint('siret'),
    )

    # You should normally *not* add any column here - see documentation above.

    def __unicode__(self):
        return u"%s - %s" % (self.siret, self.name)

    def as_json(self,
            rome_codes=None,
            hiring_type=hiring_type_util.DEFAULT,
            distance=None,
            zipcode=None,
            extra_query_string=None,
        ):
        """
        `rome_codes`: optional parameter, used only in case of being in the context
        of a search by ROME codes (single rome or multi rome).
        Without the context of ROME codes, the general purpose score of the office
        is returned.
        With the context of ROME codes, the score returned is adjusted to the ROME code,
        and the URL of the company page is also adjusted to keep the same context.
        Main case is results returned by an API search. The scores and URLs embedded
        in the company objects should be adjusted to the ROME code context.

        `hiring_type`: is needed along rome_codes to compute the right corresponding score.

        `distance` and `zipcode`: needed for potential multi geolocation logic.

        `extra_query_string` (dict): extra query string to be added to the API
        urls for each office. Typically some Google Analytics trackers.
        """
        if not isinstance(rome_codes, list) and rome_codes is not None:
            raise ValueError("rome_codes should be a list and not a string")

        if rome_codes is None:        # no rome search context
            rome_code = None
        elif len(rome_codes) == 1:    # single rome search context
            rome_code = rome_codes[0]
        else:                         # multi rome search context
            rome_code = self.matched_rome

        extra_query_string = extra_query_string or {}
        json = {
            'address': self.address_as_text,
            'city': self.city,
            'headcount_text': self.headcount_text,
            'lat': self.y,
            'lon': self.x,
            'naf': self.naf,
            'naf_text': self.naf_text,
            'name': self.name,
            'siret': self.siret,
            'stars': self.get_stars_for_rome_code(rome_code, hiring_type),
            'url': self.get_url_for_rome_code(rome_code, **extra_query_string),
            'contact_mode': util.get_contact_mode_for_rome_and_naf(rome_code, self.naf),
            'alternance': self.has_good_enough_alternance_score(),
            # Warning: the `distance` and `matched_rome` fields are added by `get_companies_from_es_and_db`,
            # they are NOT model fields or properties!
            'distance': self.distance,
        }
        if rome_codes is not None and len(rome_codes) > 1:  # only makes sense for multi rome searches
            json['matched_rome_code'] = rome_code
            json['matched_rome_label'] = settings.ROME_DESCRIPTIONS[rome_code]
            json['matched_rome_slug'] = slugify(settings.ROME_DESCRIPTIONS[rome_code])

        # This message should concern only a small number of companies who explicitly requested
        # to appear in extra geolocations.
        if any([distance, zipcode]) and json['address'] and self.show_multi_geolocations_msg(distance, zipcode):
            json['address'] += u", Cette entreprise recrute aussi dans votre région."
        return json

    @property
    def address_fields(self):
        result = []
        if not self.is_small:
            result.append(u"Service des ressources humaines")
        if self.street_name:
            result.append(u'%s %s' % (self.street_number, self.street_name))
        result.append(u'%s %s' % (self.zipcode, self.city))
        return result

    @property
    def address_as_text(self):
        if self.address_fields:
            return u", ".join([f for f in self.address_fields if f is not None])
        return None

    @property
    def phone(self):
        has_phone = self.tel and not self.tel.isspace()
        if has_phone:
            # not sure why, the import botched the phone number...
            if self.tel[-2] == u'.':
                s = u'0%s' % self.tel[:-2]
                return u" ".join(s[i:i + 2] for i in range(0, len(s), 2))
            return self.tel
        return None

    @property
    def name(self):
        if self.office_name:
            result = self.office_name.upper()
        elif self.company_name:
            result = self.company_name.upper()
        else:
            result = u'sans nom'
        return encoding_util.sanitize_string(result)

    @property
    def google_url(self):
        google_search = "%s+%s" % (self.name.replace(' ', '+'), self.city.replace(' ', '+'))
        return u"https://www.google.fr/search?q=%s" % google_search

    @property
    def kompass_url(self):
        return u"http://fr.kompass.com/searchCompanies?text=%s" % self.siret

    @property
    def headcount_text(self):
        try:
            return settings.HEADCOUNT_INSEE[self.headcount]
        except KeyError:
            return u''

    @property
    def is_small(self):
        try:
            return int(self.headcount) < settings.HEADCOUNT_SMALL_ONLY_MAXIMUM
        except (ValueError, TypeError):
            return True

    def has_city(self):
        try:
            city = bool(CITY_NAMES[self.city_code])
        except KeyError:
            if self.city_code.startswith('75'):
                city = True
            else:
                city = None
        return city

    @property
    def city(self):
        try:
            return CITY_NAMES[self.city_code].decode('utf-8')
        except KeyError:
            if self.city_code.startswith('75'):
                return u'Paris'
            else:
                raise

    @property
    def naf_text(self):
        return settings.NAF_CODES[self.naf]

    @property
    def stars(self):
        return self.get_stars_for_rome_code(None)

    def get_stars_for_rome_code(self, rome_code, hiring_type=hiring_type_util.DEFAULT):
        if hiring_type == hiring_type_util.DPAE:
            raw_score = self.score
        elif hiring_type == hiring_type_util.ALTERNANCE:
            raw_score = self.score_alternance
        else:
            raise ValueError("Unknown hiring_type.")
        score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
            score=raw_score,
            rome_code=rome_code,
            naf_code=self.naf
            )

        return scoring_util.get_stars_from_score(score)

    def get_stars_for_rome_code_as_percentage(self, rome_code):
        """
        Converts the number of stars adjusted to given rome_code to a percentage.
        """
        return (100 * self.get_stars_for_rome_code(rome_code)) / 5

    def has_good_enough_alternance_score(self):
        # Avoid importing importer_settings.SCORE_ALTERNANCE_REDUCING_MINIMUM_THRESHOLD
        # to avoid mixing importer stuff and production.
        return self.score_alternance >= 50

    @property
    def url(self):
        """
        Returns the URL of the `details` page or `None` if we are outside of a Flask's application context.
        """
        return self.get_url_for_rome_code(None)

    def get_url_for_rome_code(self, rome_code, **query_string):
        try:
            if rome_code:
                return url_for('office.details', siret=self.siret, rome_code=rome_code, _external=True, **query_string)
            else:
                return url_for('office.details', siret=self.siret, _external=True, **query_string)
        except RuntimeError:
            # RuntimeError is raised when we are outside of a Flask's application context.
            # Here, we cannot properly generate an URL via url_for.
            return None

    def show_multi_geolocations_msg(self, distance=None, zipcode=None):
        """
        Returns True if a message that indicates that the current office recruits beyond
        the boundaries of its own departement should be displayed, False otherwise.

        This message should concern only a small number of companies who explicitly requested
        to appear in extra geolocations.
        """
        if self.has_multi_geolocations:
            # If the given `zipcode` is in the same departement: the message is unnecessary.
            if zipcode and zipcode.startswith(self.zipcode[:2]):
                return False
            # If the given `distance` is too far: the message is unnecessary.
            from labonneboite.web.search.forms import CompanySearchForm
            if distance and int(distance) > int(CompanySearchForm.DISTANCE_S):
                return False
            return True
        return False

    @classmethod
    @lru_cache(maxsize=None)
    def get_date_of_last_data_deploy(cls):
        """
        Get date of when the 'etablissements' table was (re)created by the deploy_data process.

        Returns None if the information is not available.
        """
        query = """
            SELECT CREATE_TIME
                FROM information_schema.tables
                WHERE TABLE_SCHEMA = '%s'
                    AND TABLE_NAME = '%s';
        """ % (DATABASE['NAME'], settings.OFFICE_TABLE)

        last_data_deploy_date = db_session.execute(query).first()

        if last_data_deploy_date is None:
            return None

        last_data_deploy_date = last_data_deploy_date[0]

        # Formatting date in french format using locale.setlocale is strongly discouraged.
        # Using babel instead is the recommended way.
        # See https://stackoverflow.com/questions/985505/locale-date-formatting-in-python
        last_data_deploy_date_formated_as_french = format_date(last_data_deploy_date, locale='fr', format='long')
        return last_data_deploy_date_formated_as_french
