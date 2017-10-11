# coding: utf8

from functools import wraps

from flask import abort, Blueprint, current_app, jsonify, request

from labonneboite.common import geocoding
from labonneboite.common import search
from labonneboite.common import mapping as mapping_util
from labonneboite.common.load_data import load_ogr_rome_mapping
from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.web.api import util as api_util
from labonneboite.conf.common.naf_codes import NAF_CODES
from labonneboite.conf.common.settings_common import SORTING_CHOICES


apiBlueprint = Blueprint('api', __name__)

OGR_ROME_CODES = load_ogr_rome_mapping()
ROME_CODES = OGR_ROME_CODES.values()
SORTING_VALUES = [key for key, _ in SORTING_CHOICES]

# Some internal services of Pôle emploi can sometimes have access to sensitive information.
API_INTERNAL_CONSUMERS = ['labonneboite', 'memo']


def api_auth_required(function):
    """
    A decorator that checks that auth and security params are valid.
    This decorator must be used on each view of the API.
    """
    @wraps(function)
    def decorated(*args, **kwargs):

        if 'user' not in request.args:
            return u'missing argument: user', 400

        if not current_app.debug:
            try:
                api_util.check_api_request(request)
            except api_util.TimestampFormatException:
                return u'timestamp format: %Y-%m-%dT%H:%M:%S', 400
            except api_util.TimestampExpiredException:
                return u'timestamp has expired', 400
            except api_util.InvalidSignatureException:
                return u'signature is invalid', 400
            except api_util.UnknownUserException:
                return u'user is unknown', 400

        return function(*args, **kwargs)

    return decorated


# Note: `company` should be renamed to `office` wherever possible.
# Unfortunately old routes cannot change.

@apiBlueprint.route('/company/', methods=['GET'])
@api_auth_required
def company_list():
    """
    Returns a list of companies given a set of parameters.

    Required parameters:
    - `rome_codes`: one or more "Pôle emploi ROME" codes, comma separated.
    - `commune_id`: "code INSEE" of the city near which to search. If empty `latitude` and `longitude` are required.
    - `latitude` and `longitude`: coordinates of a location near which to search. If empty `commune_id` is required.

    Optional parameters:
    - `distance`: perimeter of the search radius (in Km) in which to search.
    - `page`: number of the requested page.
    - `page_size`: number of results per page (maximum : 100).
    - `naf_codes`: one or more naf_codes, comma separated. If empty or missing, no filter will be used
    """

    current_app.logger.debug("API request received: %s", request.full_path)

    city = {}
    if 'commune_id' in request.args:
        city = geocoding.get_city_by_commune_id(request.args.get('commune_id'))
        if not city:
            return u'could not resolve latitude and longitude from given commune_id', 400
        latitude = city['coords']['lat']
        longitude = city['coords']['lon']
    elif 'latitude' in request.args and 'longitude' in request.args:
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
    else:
        return u'missing arguments: either commune_id or latitude and longitude', 400

    rome_codes = request.args.get('rome_codes')
    if not rome_codes:
        return u'missing argument: rome_codes', 400

    rome_code_list = [code.upper() for code in rome_codes.split(',')]
    for rome in rome_code_list:
        if rome.encode('ascii', 'ignore') not in ROME_CODES:  # ROME_CODES contains ascii data but rome is unicode.
            return u'invalid rome code: %s' % rome, 400

    if len(rome_code_list) > 1:
        # Reasons why we only support single-rome search are detailed in README.md
        return u'Multi ROME search is no longer supported, please use single ROME search only.', 400
    rome_code = rome_code_list[0]

    try:
        page = int(request.args.get('page'))
    except TypeError:
        page = 1

    try:
        page_size = int(request.args.get('page_size'))
    except TypeError:
        page_size = 10

    if page_size > 100:
        return u'page_size is too large. Maximum value is 100', 400

    to_number = page * page_size
    from_number = to_number - page_size + 1

    try:
        distance = int(request.args.get('distance'))
    except (TypeError, ValueError):
        distance = settings.DISTANCE_FILTER_DEFAULT

    try:
        headcount_filter = int(request.args.get('headcount'))
    except (TypeError, ValueError):
        headcount_filter = settings.HEADCOUNT_WHATEVER

    naf_code_list = {}
    naf_codes = request.args.get('naf_codes')
    if naf_codes:
        naf_code_list = [naf.upper() for naf in naf_codes.split(',')]
        naf_invalid = [naf for naf in naf_code_list if naf not in NAF_CODES]
        if naf_invalid:
            return u'invalid NAF code(s): %s' % ' '.join(naf_invalid), 400

    sort = settings.SORT_FILTER_DEFAULT
    if 'sort' in request.args:
        sort = request.args.get('sort')
        if sort not in SORTING_VALUES:
            return u'invalid sort value. Possible values : %s' % ', '.join(SORTING_VALUES), 400

    companies, companies_count = search.get_companies(
        naf_codes,
        rome_code,
        latitude,
        longitude,
        distance,
        headcount_filter=headcount_filter,
        from_number=from_number,
        to_number=to_number,
        sort=sort,
        index=settings.ES_INDEX,
    )

    result = {
        'companies': [
            company.as_json(rome_code=rome_code, distance=distance, zipcode=city.get('zipcode'))
            for company in companies
        ],
        'companies_count': companies_count
    }
    return jsonify(result)


@apiBlueprint.route('/office/<siret>/details', methods=['GET'])
@api_auth_required
def office_details(siret):
    """
    Returns the details of an office for the given <siret> number.
    """
    office = Office.query.filter_by(siret=siret).first()
    if not office:
        abort(404)
    result = {
        'headcount_text': office.headcount_text,
        'lat': office.y,
        'lon': office.x,
        'naf': office.naf,
        'naf_text': office.naf_text,
        'name': office.name,
        'siret': office.siret,
        'stars': office.stars,
        'url': office.url,
        'address': {
            'city': office.city,
            'city_code': office.city_code,
            'street_name': office.street_name,
            'street_number': office.street_number,
            'zipcode': office.zipcode,
        },
    }
    if request.args['user'] in API_INTERNAL_CONSUMERS:
        result['email'] = office.email
        result['phone'] = office.tel
        result['website'] = office.website
    return jsonify(result)
