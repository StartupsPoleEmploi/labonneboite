# coding: utf8
import datetime
import json
import re

from dateutil.relativedelta import relativedelta
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy import Column, ForeignKey
from sqlalchemy import desc
from sqlalchemy.event import listens_for
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from labonneboite.common import geocoding
from labonneboite.common.database import Base
from labonneboite.common.models import OfficeMixin
from labonneboite.common.models.base import CRUDMixin
from labonneboite.conf import settings


class OfficeAdminAdd(OfficeMixin, CRUDMixin, Base):
    """
    Upon requests received from employers, we can add some offices.
    This can be offices which are not included in the data provided
    by the importer, e.g. offices without hiring history.

    This model must have the same fields as the `Office` model which
    are provided by the `OfficeMixin`.
    """

    __tablename__ = 'etablissements_admin_add'

    def __init__(self, *args, **kwargs):
        # The `headcount` field must be different form the one of `Office`
        # to be able to provide a clean <select> choice in the admin UI.
        self.headcount = Column('trancheeffectif', ChoiceType(settings.HEADCOUNT_INSEE_CHOICES), default=u"00",
            nullable=False,)
        super(OfficeAdminAdd, self).__init__(*args, **kwargs)

    id = Column(Integer, primary_key=True)

    # Some fields that must be common with the `Office` model are provided by the `OfficeMixin`.

    reason = Column(Text, default='', nullable=False)  # Reason of the addition.
    # Metadata.
    date_created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html
    created_by = relationship('User', foreign_keys=[created_by_id])
    updated_by = relationship('User', foreign_keys=[updated_by_id])

    __mapper_args__ = {
        'order_by': desc(date_created),  # Default order_by for all queries.
    }


class OfficeAdminRemove(CRUDMixin, Base):
    """
    Upon requests received from employers, we can remove some offices.
    This model collects the list of offices to remove.
    """

    __tablename__ = 'etablissements_admin_remove'

    INITIATIVE_OFFICE = u'office'
    INITIATIVE_LBB = u'lbb'
    INITIATIVE_CHOICES = [
        (INITIATIVE_OFFICE, u"L'entreprise"),
        (INITIATIVE_LBB, u"La Bonne Boite"),
    ]

    id = Column(Integer, primary_key=True)
    siret = Column(String(191), nullable=False, unique=True)
    name = Column(String(191), default='', nullable=False)
    reason = Column(Text, default='', nullable=False)  # Reason of the removal.
    initiative = Column(ChoiceType(INITIATIVE_CHOICES), default=INITIATIVE_OFFICE, nullable=False)
    date_follow_up_phone_call = Column(DateTime, nullable=True)

    # Removal requested by.
    requested_by_email = Column(String(191), default='', nullable=False)
    requested_by_first_name = Column(String(191), default='', nullable=False)
    requested_by_last_name = Column(String(191), default='', nullable=False)
    requested_by_phone = Column(String(191), default='', nullable=False)

    # Metadata.
    date_created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html
    created_by = relationship('User', foreign_keys=[created_by_id])
    updated_by = relationship('User', foreign_keys=[updated_by_id])

    __mapper_args__ = {
        'order_by': desc(date_created),  # Default order_by for all queries.
    }


class OfficeAdminUpdate(CRUDMixin, Base):
    """
    Upon requests received from employers, we can update some offices info.
    This model collects the changes to apply to offices.
    """

    __tablename__ = 'etablissements_admin_update'

    SEPARATORS = [u'\n', u'\r']

    id = Column(Integer, primary_key=True)

    # Stores a list of SIRET as a string separated by `SEPARATORS`
    sirets = Column(Text, default='', nullable=False, unique=False)

    name = Column(String(191), default='', nullable=False)

    # Info to update.
    new_email = Column(String(191), default='', nullable=False)
    email_alternance = Column(String(191), default='', nullable=False)
    new_phone = Column(String(191), default='', nullable=False)
    new_website = Column(String(191), default='', nullable=False)

    # Set `boost` to True to promote the office for LBB.
    # Set `boost_alternance` to True to promote the office for alternance.
    boost = Column(Boolean, default=False, nullable=False)
    boost_alternance = Column(Boolean, default=False, nullable=False)

    # Stores a list of ROME codes as a string separated by `SEPARATORS`.
    # If `romes_to_boost` is populated, boosting will be set only for specified ROME codes for LBB.
    # If `romes_alternance_to_boost` is populated, boosting will be set only for specified ROME codes for alternance.
    romes_to_boost = Column(Text, default='', nullable=False)
    romes_alternance_to_boost = Column(Text, default='', nullable=False)

    # Stores a list of ROME codes as a string separated by `SEPARATORS`.
    # If `romes_to_remove` is populated, these ROME codes will not be indexed for LBB
    # If `romes_alternance_to_remove` is populated, these ROME codes will not be indexed for alternance
    romes_to_remove = Column(Text, default='', nullable=False)
    romes_alternance_to_remove = Column(Text, default='', nullable=False)

    # Stores a list of NAF codes as a string separated by `SEPARATORS`.
    # If `nafs_to_add` is populated, all the romes associated to this NAF will be added.
    nafs_to_add = Column(Text, default='', nullable=False)

    # Info to remove.
    remove_email = Column(Boolean, default=False, nullable=False)
    remove_phone = Column(Boolean, default=False, nullable=False)
    remove_website = Column(Boolean, default=False, nullable=False)

    # Hide company visibility depending of the hyring type
    new_score = Column(Integer, default=False, nullable=False)
    new_score_alternance = Column(Integer, default=False, nullable=False)

    # Update requested by.
    requested_by_email = Column(String(191), default='', nullable=False)
    requested_by_first_name = Column(String(191), default='', nullable=False)
    requested_by_last_name = Column(String(191), default='', nullable=False)
    requested_by_phone = Column(String(191), default='', nullable=False)

    reason = Column(Text, default='', nullable=False)  # Reason of the update.
    # Metadata.
    date_created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html
    created_by = relationship('User', foreign_keys=[created_by_id])
    updated_by = relationship('User', foreign_keys=[updated_by_id])

    __mapper_args__ = {
        'order_by': desc(date_created),  # Default order_by for all queries.
    }

    def clean(self):
        """
        Clean some fields before saving or updating the instance.
        This method should not be called manually since it's automatically triggered
        on a `before_insert` or `before_update` event via `listens_for`.
        """
        # Remove multiple newlines in `romes_to_boost`.
        separator = self.SEPARATORS[0]
        self.romes_to_boost = separator.join(self.as_list(self.romes_to_boost))

    @staticmethod
    def as_list(codes):
        """
        Converts the given string of codes to a Python list of unique codes.
        """
        if not codes:
            return []
        separators = OfficeAdminUpdate.SEPARATORS
        codes = [v.strip() for v in re.split('|'.join(separators), codes) if v.strip()]
        return sorted(set(codes))

    def romes_as_html(self, romes):
        """
        Returns the content of the `romes_to_boost` field as HTML.
        Used in the admin UI.
        """
        html = []
        for rome in self.as_list(romes):
            html.append(u"{0} - {1}".format(rome, settings.ROME_DESCRIPTIONS[rome]))
        return '<br>'.join(html)


class OfficeAdminExtraGeoLocation(CRUDMixin, Base):
    """
    Upon requests received from employers, we can add some geolocations to offices.
    This allows companies that hire to appear in multiple locations.
    """

    __tablename__ = 'etablissements_admin_extra_geolocations'

    GEOLOCATIONS_TEXT_SEPARATORS = [u'\n', u'\r']

    id = Column(Integer, primary_key=True)
    siret = Column(String(191), nullable=False, unique=True)

    # Stores a list of french "codes communes (INSEE)" and/or french "departements" as a string
    # separated by `GEOLOCATIONS_TEXT_SEPARATORS`.
    codes = Column(Text, nullable=False)
    # Stores a JSON object of latitude/longitude coordinates found in each entry of `self.codes`.
    geolocations = Column(Text, nullable=False)
    # After this date, extra geolocations will be considered obsolete.
    date_end = Column(DateTime, default=datetime.datetime.utcnow() + relativedelta(months=3), nullable=False)

    reason = Column(Text, default='', nullable=False)

    # Metadata.
    date_created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html
    created_by = relationship('User', foreign_keys=[created_by_id])
    updated_by = relationship('User', foreign_keys=[updated_by_id])

    __mapper_args__ = {
        'order_by': desc(date_created),  # Default order_by for all queries.
    }

    def clean(self):
        """
        Clean some fields before saving or updating the instance.
        This method should not be called manually since it's automatically triggered
        on a `before_insert` or `before_update` event via `listens_for`.
        """
        # Remove multiple newlines in `codes`.
        separator = self.GEOLOCATIONS_TEXT_SEPARATORS[0]
        self.codes = separator.join(self.codes_as_list(self.codes))
        # Get and store the content of `geolocations` as JSON.
        self.geolocations = self.codes_as_json_geolocations(self.codes)

    def is_outdated(self):
        """
        Returns True if extra geolocations are outdated, False otherwise.
        """
        return datetime.datetime.utcnow() > self.date_end

    def geolocations_as_lat_lon_properties(self):
        """
        Returns the content of the `geolocations` field as a Python list of `lat/lon dicts`.
        This stucture maps to an Elasticsearch's geo_point "Lat Lon as Properties" format.
        E.g.:
        [
            {"lat" : 48.85, "lon" : 2.35},
            {"lat" : 48.86, "lon" : 2.35},
        ]
        """
        return sorted([{'lat': coords[0], 'lon': coords[1]} for coords in json.loads(self.geolocations)])

    def geolocations_as_html_links(self):
        """
        Returns the content of the `geolocations` field as HTML links.
        Used in the admin UI.
        """
        html = []
        link = u'<a href="https://maps.google.com/maps?q={lat},{lon}" target="_blank">{lat}, {lon}</a>'
        for coords in self.geolocations_as_lat_lon_properties():
            html.append(link.format(lat=coords['lat'], lon=coords['lon']))
        return u'<br>'.join(html)

    @staticmethod
    def codes_as_list(codes):
        """
        Converts the given string of codes to a Python list of unique codes.
        """
        if not codes:
            return []
        separators = OfficeAdminExtraGeoLocation.GEOLOCATIONS_TEXT_SEPARATORS
        codes = [v.strip() for v in re.split('|'.join(separators), codes) if v.strip()]
        return sorted(set(codes))

    @staticmethod
    def codes_as_geolocations(codes):
        """
        Converts the given string of codes to an array of `lat/lon tuples`.
        E.g.:
        [
            (48.68, 6.17),
            (49.15, 6.22),
        ]
        """
        geolocations = []
        codes_list = OfficeAdminExtraGeoLocation.codes_as_list(codes)
        for code in codes_list:
            if geocoding.is_departement(code):
                for city in geocoding.get_all_cities_from_departement(code):
                    geolocations.append((city['coords']['lat'], city['coords']['lon']))
            elif geocoding.is_commune_id(code):
                city = geocoding.get_city_by_commune_id(code)
                geolocations.append((city['coords']['lat'], city['coords']['lon']))
        return geolocations

    @staticmethod
    def codes_as_json_geolocations(codes):
        """
        Converts the given string of codes to a JSON object suitable to be stored in the `geolocations` field.
        E.g.:
        '[[48.68, 6.17], [49.15, 6.22]]'
        """
        return json.dumps(OfficeAdminExtraGeoLocation.codes_as_geolocations(codes))


@listens_for(OfficeAdminUpdate, 'before_insert')
@listens_for(OfficeAdminUpdate, 'before_update')
@listens_for(OfficeAdminExtraGeoLocation, 'before_insert')
@listens_for(OfficeAdminExtraGeoLocation, 'before_update')
def clean(mapper, connect, self):
    """
    Trigger the `clean()` method before an insert or an update.
    """
    self.clean()
