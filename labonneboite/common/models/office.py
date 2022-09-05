from functools import lru_cache
import logging
from typing import Any, Optional, Sequence, Dict, Union, Mapping, Set, List
from decimal import Decimal

from babel.dates import format_date
from flask import url_for
from slugify import slugify
from sqlalchemy import PrimaryKeyConstraint, Index
from werkzeug import cached_property
from labonneboite_common import encoding as encoding_util

from labonneboite.common import hiring_type_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common import scoring as scoring_util
from labonneboite.common import util
from labonneboite.common.database import Base, db_session, DATABASE
from labonneboite.common.load_data import load_city_codes, load_groupements_employeurs
from labonneboite.common.mapping import RomeTuple
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common.conf import settings
from labonneboite.common.models import FinalOfficeMixin, OfficeAdminUpdate
from labonneboite.common.scoring import get_score_from_hirings

logger = logging.getLogger('main')

CITY_NAMES = load_city_codes()

JsonType = Mapping[str, Union[str, None, int, bool, float, Optional[Sequence[Mapping[str, Union[str, int]]]]]]


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

    Then, be sure to double check that both labonneboite-importer project and
    `make test_all` complete successfully.
    """
    __tablename__ = settings.OFFICE_TABLE

    __table_args__ = (
        PrimaryKeyConstraint('siret'),

        # Improve performance of create_index.py parallel jobs
        # by quickly fetching all offices of any given departement.
        Index('_departement', 'departement'),

        # Improve performance of create_index.py remove_scam_emails()
        # by quickly locating offices having a given scam email.
        Index('_email', 'email'),
    )

    # You should normally *not* add any column here - see documentation above.

    def __unicode__(self) -> str:
        return "%s - %s" % (self.siret, self.name)

    def as_json(
            self,
            rome_codes: Optional[Sequence[str]] = None,
            hiring_type: Optional[str] = None,
            distance: Optional[int] = None,
            zipcode: Optional[str] = None,
            extra_query_string: Optional[Dict[str, Any]] = None,
    ) -> JsonType:
        """
        `rome_codes`: optional parameter, used only in case of being in the context
        of a search by ROME codes (single rome or multi rome).
        Without the context of ROME codes, the general purpose score of the office
        is returned.
        With the context of ROME codes, the score returned is adjusted to the ROME code,
        and the URL of the company page is also adjusted to keep the same context.
        Main case is results returned by an API search. The scores and URLs embedded
        in the company objects should be adjusted to the ROME code context.

        `hiring_type`: is needed along rome_codes to compute the right corresponding score,
        possible values are hiring_type_util.VALUES

        `distance` and `zipcode`: needed for potential multi geolocation logic.

        `extra_query_string` (dict): extra query string to be added to the API
        urls for each office. Typically some Google Analytics trackers.
        """
        rome_code = self.get_matched_rome(rome_codes)

        alternance = hiring_type == hiring_type_util.ALTERNANCE

        extra_query_string = extra_query_string or {}
        json: Dict[str, Union[str, float, int, None]] = dict(
            address=self.address_as_text,
            city=self.city,
            headcount_text=self.headcount_text,
            lat=float(self.y),
            lon=float(self.x),
            naf=self.naf,
            naf_text=self.naf_text,
            name=self.name,
            siret=self.siret,
            stars=self.get_stars_for_rome_code(rome_code),
            url=self.get_url_for_rome_code(rome_code, alternance, **extra_query_string),
            contact_mode=util.get_contact_mode_for_rome_and_office(rome_code, self),
            social_network=self.social_network or '',
            alternance=False,
        )

        # Warning: the `distance`, `boost` and `matched_rome` fields are added by `get_offices_from_es_and_db`,
        # they are NOT model fields or properties!
        if rome_code:
            json['matched_rome_code'] = rome_code
            json['matched_rome_label'] = settings.ROME_DESCRIPTIONS[rome_code]
            json['matched_rome_slug'] = slugify(settings.ROME_DESCRIPTIONS[rome_code])

        # offers* fields are added by VisibleMarketFetcher.get_offices,
        # they are NOT model fields or properties
        # This message should concern only a small number of companies who explicitly requested
        # to appear in extra geolocations.
        if any([distance, zipcode]) and self.address_as_text and self.show_multi_geolocations_msg(zipcode):
            json['address'] = self.address_as_text + ", Cette entreprise recrute aussi dans votre région."
        return json

    @property
    def score(self) -> 'Decimal':
        return Decimal(get_score_from_hirings(self.hiring))

    def get_matched_rome(self, rome_codes: Sequence[str]) -> Optional[str]:
        if rome_codes is None:  # no rome search context
            rome_code = None
        elif len(rome_codes) == 1:  # single rome search context
            rome_code = rome_codes[0]
        else:
            raise NotImplementedError()
        return rome_code

    @property
    def address_fields(self) -> Sequence[str]:
        result = []
        if not self.is_small:
            result.append("Service des ressources humaines")
        if self.street_name:
            result.append('%s %s' % (self.street_number, self.street_name))
        result.append('%s %s' % (self.zipcode, self.city))
        return result

    @property
    def address_as_text(self) -> Optional[str]:
        if self.address_fields:
            return ", ".join([f for f in self.address_fields if f is not None])
        return None

    @property
    def phone(self) -> Optional[str]:
        has_phone = self.tel and not self.tel.isspace()
        if has_phone:
            # not sure why, the import botched the phone number...
            if self.tel[-2] == '.':
                s = '0%s' % self.tel[:-2]
                return " ".join(s[i:i + 2] for i in range(0, len(s), 2))
            return self.tel
        return None

    @property
    def name(self) -> str:
        if self.office_name:
            result = self.office_name.upper()
        elif self.company_name:
            result = self.company_name.upper()
        else:
            result = 'sans nom'
        return encoding_util.sanitize_string(result)

    @property
    def google_url(self) -> str:
        google_search = "%s+%s" % (self.name.replace(' ', '+'), self.city.replace(' ', '+'))
        return "https://www.google.fr/search?q=%s" % google_search

    @property
    def kompass_url(self) -> str:
        return "http://fr.kompass.com/searchCompanies?text=%s" % self.siret

    @property
    def is_groupement_employeurs(self) -> bool:
        """
        A "groupement d'employeurs" is a French-only juridical entity
        which is basically a collection of offices.
        """
        return self.siret in load_groupements_employeurs()

    @property
    def is_removed_from_lba(self) -> bool:
        """
        Returns True if the company has explicitly asked via SAVE
        to be removed from LBA.
        """
        if self.score_alternance > 0:
            return False
        # office.score_alternance == 0 does not guarantee the office has
        # been removed via SAVE from LBA as many offices "naturally" have
        # such a score.
        # We still have to check that there actually is a SAVE record
        # specifically asking for this removal.
        office_admin_update = OfficeAdminUpdate.query.filter(OfficeAdminUpdate.sirets.like("%{}%".format(
            self.siret))).filter_by(score_alternance=0).first()
        return bool(office_admin_update)

    @property
    def headcount_text(self) -> str:
        try:
            return settings.HEADCOUNT_INSEE[self.headcount]
        except KeyError:
            return ''

    @property
    def is_small(self) -> bool:
        try:
            return int(self.headcount) < settings.HEADCOUNT_SMALL_ONLY_MAXIMUM
        except (ValueError, TypeError):
            return True

    def has_city(self) -> bool:
        try:
            city = bool(CITY_NAMES[self.city_code])
        except KeyError:
            if self.city_code.startswith('75'):
                city = True
            else:
                city = None
        return city

    @property
    def city(self) -> str:
        try:
            return CITY_NAMES[self.city_code]  # type: ignore
        except KeyError:
            if self.city_code.startswith('75'):
                return 'Paris'
            else:
                raise

    @property
    def naf_text(self) -> str:
        return settings.NAF_CODES[self.naf]  # type: ignore

    @property
    def stars(self) -> float:
        return self.get_stars_for_rome_code(None)

    @cached_property
    def romes_for_naf_mapping(self) -> List[RomeTuple]:
        """
        Returns a list of named tuples for ROME codes matching the company's NAF code.
        """
        return mapping_util.romes_for_naf(self.naf)

    @cached_property
    def romes_codes(self) -> Set[str]:
        """
        Returns the default set of ROME codes for the current company.
        """
        return set([rome.code for rome in self.romes_for_naf_mapping])

    def get_score_for_rome_code(self, rome_code: Optional[str]) -> int:
        return scoring_util.get_score_adjusted_to_rome_code_and_naf_code(rome_code=rome_code,
                                                                         naf_code=self.naf,
                                                                         hiring=self.hiring)

    def get_stars_for_rome_code(self, rome_code: Optional[str]) -> float:
        score = self.get_score_for_rome_code(rome_code)
        return scoring_util.get_stars_from_score(score)

    def get_stars_for_rome_code_as_percentage(self, rome_code: Optional[str]) -> float:
        """
        Converts the number of stars adjusted to given rome_code to a percentage.
        """
        return (100 * self.get_stars_for_rome_code(rome_code)) / 5

    @property
    def url(self) -> Optional[str]:
        """
        Returns the URL of the `details` page or `None` if we are outside of a Flask's application context.
        """
        return self.get_url_for_rome_code(None)

    def get_url_for_rome_code(self, rome_code: Optional[str], alternance: bool = False, **query_string: Any
                              ) -> Optional[str]:
        try:
            if rome_code:
                return url_for('office.details',
                               siret=self.siret,
                               rome_code=rome_code,
                               _external=True,
                               contract='alternance' if alternance else None,
                               **query_string)
            return url_for('office.details',
                           siret=self.siret,
                           contract='alternance' if alternance else None,
                           _external=True,
                           **query_string)
        except RuntimeError:
            # RuntimeError is raised when we are outside of a Flask's application context.
            # Here, we cannot properly generate an URL via url_for.
            return None

    def show_multi_geolocations_msg(self, zipcode: Optional[str] = None) -> bool:
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
            return True
        return False

    @classmethod
    @lru_cache(maxsize=None)
    def get_date_of_last_data_deploy(cls) -> Optional[str]:
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
        last_data_deploy_date_formated_as_french: str = format_date(last_data_deploy_date, locale='fr', format='long')
        return last_data_deploy_date_formated_as_french


class OfficeResult(Office):
    __abstract__ = True

    matched_rome: Optional[str] = None
    distance: Optional[float] = None
    boost: Optional[bool] = False
    offers_count: int
    position: int
    offers: Optional[Sequence[Dict[str, Union[str, int]]]]

    def __init__(self,
                 office: Optional[Office] = None,
                 *,
                 offers_count: Optional[int] = None,
                 position: Optional[int] = None,
                 matched_rome: Optional[str] = None,
                 distance: Optional[float] = None,
                 boost: Optional[bool] = False,
                 offers: Optional[Sequence[Dict[str, Union[str, int]]]] = None,
                 **kwargs: Any) -> None:
        # set office props in kwargs (to __init__ the super class)
        office_props = {}
        if office is not None:
            office_props = dict(office.__dict__)
            office_props.pop('_sa_instance_state', None)  # added by : self.__dict__
        office_props.update(kwargs)
        super(OfficeResult, self).__init__(**office_props)
        self.matched_rome = matched_rome
        self.distance = distance
        self.boost = boost
        self.offers_count = offers_count
        self.position = position
        self.offers = offers

    def as_json(
            self,
            rome_codes: Optional[Sequence[str]] = None,
            hiring_type: Optional[str] = None,
            distance: Optional[int] = None,
            zipcode: Optional[str] = None,
            extra_query_string: Optional[Dict[str, Any]] = None,
    ) -> JsonType:
        json = dict(super().as_json(rome_codes=rome_codes, hiring_type=hiring_type, distance=distance, zipcode=zipcode,
                                    extra_query_string=extra_query_string))
        if self.distance is not None:
            json['distance'] = self.distance

        json['boosted'] = self.boost
        if self.offers_count is not None:
            json['offers_count'] = self.offers_count

        if self.offers is not None:
            json['offers'] = self.offers

        return json

    def get_matched_rome(self, rome_codes: Sequence[str]) -> Optional[str]:
        if rome_codes is None:  # no rome search context
            rome_code = None
        elif len(rome_codes) == 1:  # single rome search context
            rome_code = rome_codes[0]
        else:  # multi rome search context
            rome_code = self.matched_rome
        return rome_code
