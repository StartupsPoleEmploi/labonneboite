# coding: utf8

from __future__ import division
import logging

from flask import url_for
from sqlalchemy import Column, Index, Integer, String, Float, Boolean
from sqlalchemy import exists, PrimaryKeyConstraint

from labonneboite.common import encoding as encoding_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common.database import Base, db_session
from labonneboite.common.load_data import load_city_codes
from labonneboite.common.models.base import CRUDMixin
from labonneboite.conf import settings


logger = logging.getLogger('main')


CITY_NAMES = load_city_codes()


class OfficeMixin(object):
    """
    This mixin provides the fields that must be common between the `Office`
    model and the `OfficeAdminAdd` model.

    Don't forget to create a new migration for `OfficeAdminAdd` when you add
    or remove a field here to keep models in sync.
    """
    siret = Column('siret', String(191))
    company_name = Column('raisonsociale', String(191), nullable=False)
    office_name = Column('enseigne', String(191), default='', nullable=False)
    naf = Column('codenaf', String(8), nullable=False)
    street_number = Column('numerorue', String(191), default='', nullable=False)
    street_name = Column('libellerue', String(191), default='', nullable=False)
    city_code = Column('codecommune', String(191), nullable=False)
    zipcode = Column('codepostal', String(8), nullable=False)
    email = Column('email', String(191), default='', nullable=False)
    tel = Column('tel', String(191), default='', nullable=False)
    website = Column('website', String(191), default='', nullable=False)
    flag_alternance = Column(Boolean, default=False, nullable=False)
    flag_junior = Column(Boolean, default=False, nullable=False)
    flag_senior = Column(Boolean, default=False, nullable=False)
    flag_handicap = Column(Boolean, default=False, nullable=False)
    departement = Column('departement', String(8), nullable=False)
    headcount = Column('trancheeffectif', String(2))
    score = Column('score', Integer, default=0, nullable=False)
    x = Column('coordinates_x', Float, nullable=False)  # Longitude.
    y = Column('coordinates_y', Float, nullable=False)  # Latitude.


class Office(OfficeMixin, CRUDMixin, Base):
    """
    An office.

    Warning: this model is currently excluded from the migration system
    because it's entirely dropped and recreated during an import process.
    """

    __tablename__ = settings.OFFICE_TABLE
    __table_args__ = (
        Index('dept_i', 'departement'),
        PrimaryKeyConstraint('siret'),
    )

    # Fields are provided by the `OfficeMixin`.

    def __unicode__(self):
        return u"%s - %s" % (self.siret, self.name)

    def as_json(self, rome_code=None):
        """
        rome_code : optional parameter, used only in case of being in the context
        of a search by ROME code.
        Without the context of a ROME code, the general purpose score of the office
        is returned.
        With the context of a ROME code, the score returned is adjusted to the ROME code,
        and the URL of the company page is also adjusted to keep the same context.
        Main case is results returned by an API search. The scores and URLs embedded
        in the company objects should be adjusted to the ROME code context.

        TOFIX: some fields are added by external functions. This limits considerably
        the usefulness of this method.
        """
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
            'stars': self.get_stars_for_rome_code(rome_code),
            'url': self.get_url_for_rome_code(rome_code),
            # Warning: the `distance` field is added by `retrieve_companies_from_elastic_search`,
            # this is NOT a model field or property!
            'distance': self.distance,
        }
        return json

    def serialize(self):
        return {
            'siret': self.siret,
            'raisonsociale': self.company_name,
            'enseigne': self.office_name,
            'codenaf': self.naf,
            'numerorue': self.street_number,
            'libellerue': self.street_name,
            'codecommune': self.city_code,
            'codepostal': self.zipcode,
            'email': self.email,
            'tel': self.phone,
            'departement': self.departement,
            'trancheeffectif': self.headcount,
            'score': self.score,
            'coordinates_x': self.x,
            'coordinates_y': self.y
        }

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
        if len(self.address_fields) >= 1:
            return u", ".join([f for f in self.address_fields if f is not None])
        else:
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

    def get_stars_for_rome_code(self, rome_code):
        """
        Converts the score (int from 0 to 100) to a number of stars (float from 0.0 and 5.0).
        In case a rome_code is given, instead of using general all-jobs-included score,
        use the score adjusted to the given rome_code.
        """
        score = scoring_util.get_score_adjusted_to_rome_code_and_naf_code(
            score=self.score,
            rome_code=rome_code,
            naf_code=self.naf
            )
        stars_num = score / (100 / 5)
        if stars_num < 0.0 or stars_num > 5.0:
            raise Exception("unexpected starts_num value %s for siret %s and rome_code %s" % (
                stars_num,
                self.siret,
                rome_code
                ))
        return stars_num

    def get_stars_for_rome_code_as_percentage(self, rome_code):
        """
        Converts the number of stars adjusted to given rome_code to a percentage.
        """
        return (100 * self.get_stars_for_rome_code(rome_code)) / 5

    @property
    def url(self):
        """
        Returns the URL of the `details` page or `None` if we are outside of a Flask's application context.
        """
        return self.get_url_for_rome_code(None)

    def get_url_for_rome_code(self, rome_code):
        try:
            if rome_code:
                return url_for('office.details', siret=self.siret, rome_code=rome_code, _external=True)
            else:
                return url_for('office.details', siret=self.siret, _external=True)
        except RuntimeError:
            # RuntimeError is raised when we are outside of a Flask's application context.
            # Here, we cannot properly generate an URL via url_for.
            return None

    def show_recruit_elsewhere_msg(self, distance, zipcode):
        """
        Returns True if a message that indicates that the current office recruits beyond the boundaries
        of its own zipcode should be displayed, False otherwise.
        This method is used in the context of the search result page.
        """
        # If the distance scope of the search is too large, the message is unnecessary.
        from labonneboite.web.search.forms import CompanySearchForm
        if distance and distance >= CompanySearchForm.DISTANCE_S:
            return False
        # If the `zipcode` search parameter is in the same departement as the current office,
        # the message is unnecessary.
        if zipcode.startswith(self.zipcode[:2]):
            return False
        # Otherwise check if this office has multi geolocations.
        # This perform 1 SQL query for each call. It might be "denormalized" if it becomes a problem.
        from labonneboite.common.models import OfficeAdminExtraGeoLocation
        return db_session.query(exists().where(OfficeAdminExtraGeoLocation.siret == self.siret)).scalar()


CONTACT_MODE_STAGES = {
    u"Se présenter spontanément": [
        u"Se présenter à l'adresse indiquée avec CV et photo",
        u"Demander le nom d'un contact pour relancer",
        u"Relancer votre interlocuteur par téléphone",
        u"Déclarer votre reprise d'emploi à Pôle emploi :-)",
    ],
    u"Envoyer un CV et une lettre de motivation": [
        (u"Rechercher le nom d'un contact dans l'entreprise (google, kompass, linkedin, viadeo, votre réseau) "
            u"pour lui adresser votre courrier/email"),
        (u"Rechercher des informations économiques (projet, évolution) sur l'entreprise afin de personnaliser "
            u"votre lettre de motivation"),
        u"Envoyer votre CV et votre lettre de motivation",
        u"Relancer votre interlocuteur par téléphone",
        u"Préparer votre entretien",
        u"Déclarer votre reprise d'emploi à Pôle emploi :-)",
    ]
}

CONTACT_MODE_DEFAULT = u"Envoyer un CV et une lettre de motivation"
