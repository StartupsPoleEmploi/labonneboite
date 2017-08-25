# coding: utf8
import datetime
import json
import re

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
        (INITIATIVE_LBB, u"La Bonne Boîte"),
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

    id = Column(Integer, primary_key=True)
    siret = Column(String(191), nullable=False, unique=True)
    name = Column(String(191), default='', nullable=False)

    # Info to update.
    new_score = Column(Integer, nullable=True)  # Set it to 100 to promote the offfice.
    new_email = Column(String(191), default='', nullable=False)
    new_phone = Column(String(191), default='', nullable=False)
    new_website = Column(String(191), default='', nullable=False)

    # Info to remove.
    remove_email = Column(Boolean, default=False, nullable=False)
    remove_phone = Column(Boolean, default=False, nullable=False)
    remove_website = Column(Boolean, default=False, nullable=False)

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


class OfficeAdminExtraGeoLocation(CRUDMixin, Base):
    """
    Upon requests received from employers, we can add some geolocations to offices.
    This allows companies that hire to appear in multiple locations.
    """

    __tablename__ = 'etablissements_admin_extra_geolocations'

    GEOLOCATIONS_TEXT_SEPARATORS = [u'\n', u'\r']

    id = Column(Integer, primary_key=True)
    siret = Column(String(191), nullable=False, unique=True)

    # Stores a list of french "zipcodes" and/or "departements" as a string separated by `GEOLOCATIONS_TEXT_SEPARATORS`.
    codes = Column(Text, nullable=False)
    # Stores a JSON object of latitude/longitude coordinates for each entry in `geolocations_text`.
    geolocations = Column(Text, nullable=False)

    reason = Column(Text, default='', nullable=False)

    # Metadata.
    date_created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html
    created_by = relationship('User', foreign_keys=[created_by_id])
    updated_by = relationship('User', foreign_keys=[updated_by_id])

    def clean(self):
        """
        Clean some fields before saving or updating the instance.
        This method should not be called manually since it's automatically triggered
        on a `before_insert` or `before_update` event via `listens_for`.
        """
        # Remove multiple newlines in `codes`.
        self.codes = '\n'.join(self.codes_as_list(self.codes))
        # Get and store the content of `geolocations` as JSON.
        self.geolocations = self.codes_as_json_geolocations(self.codes)

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
        """
        links = []
        link = '<a href="https://maps.google.com/maps?q={lat},{lon}" target="_blank">{lat}, {lon}</a>'
        for coords in self.geolocations_as_lat_lon_properties():
            links.append(link.format(lat=coords['lat'], lon=coords['lon']))
        return '<br>'.join(links)

    @staticmethod
    def is_departement(value):
        """
        Returns true if the given value is a departement, false otherwise.
        """
        return len(value) == 2

    @staticmethod
    def is_zipcode(value):
        """
        Returns true if the given value is a zipcode, false otherwise.
        """
        return len(value) == 5

    @staticmethod
    def codes_as_list(codes):
        """
        Converts the given string of codes to a Python list of codes.
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
            ('48.68', '6.17'),
            ('49.15', '6.22'),
        ]
        """
        geolocations = []
        codes_list = OfficeAdminExtraGeoLocation.codes_as_list(codes)
        for code in codes_list:
            if OfficeAdminExtraGeoLocation.is_departement(code):
                geolocations.extend(geocoding.get_all_lat_long_from_departement(code))
            elif OfficeAdminExtraGeoLocation.is_zipcode(code):
                geolocations.append(geocoding.get_lat_long_from_zipcode(code))
        return geolocations

    @staticmethod
    def codes_as_json_geolocations(codes):
        """
        Converts the given string of codes to a JSON object suitable to be stored in the `geolocations` field.
        E.g.:
        '[["48.68", "6.17"], ["49.15", "6.22"]]'
        """
        return json.dumps(OfficeAdminExtraGeoLocation.codes_as_geolocations(codes))


@listens_for(OfficeAdminExtraGeoLocation, 'before_insert')
@listens_for(OfficeAdminExtraGeoLocation, 'before_update')
def clean(mapper, connect, self):
    """
    Trigger the `OfficeAdminExtraGeoLocation.clean()` method before an insert or an update.
    """
    self.clean()
