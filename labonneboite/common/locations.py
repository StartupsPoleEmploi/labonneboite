from collections import namedtuple
import logging

from slugify import slugify

from labonneboite.common import geocoding


logger = logging.getLogger('main')


class Location(object):
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return "lon: {} - lat: {}".format(self.longitude, self.latitude)


class CityLocation(object):

    def __init__(self, zipcode, name=''):
        self.zipcode = zipcode

        # Location attribute may be None if slug/zipcode combination is incorrect
        self.location = None
        self.slug = slugify(name)
        self.name = name

        city = geocoding.get_city_by_zipcode(self.zipcode, slug=self.slug)
        if not city:
            logger.debug("unable to retrieve a city for zipcode `%s` and slug `%s`", self.zipcode, self.slug)
        else:
            coordinates = city['coords']
            self.location = Location(coordinates['lat'], coordinates['lon'])
            self.slug = city['slug']
            self.name = city['name']

    @property
    def full_name(self):
        return '%s (%s)' % (self.name, self.zipcode)

    @property
    def is_location_correct(self):
        return self.location is not None


NamedLocation = namedtuple('NamedLocation', [
    'zipcode',
    'city',
    'name',
    'city_code'
])
