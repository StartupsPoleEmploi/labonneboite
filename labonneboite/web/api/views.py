# coding: utf8

from functools import wraps

from flask import abort, Blueprint, current_app, jsonify, request

from labonneboite.common import geocoding
from labonneboite.common import search
from labonneboite.common import sorting
from labonneboite.common import mapping as mapping_util
from labonneboite.common.load_data import load_ogr_rome_mapping
from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.web.api import util as api_util
from labonneboite.conf.common.settings_common import CONTRACT_VALUES, HEADCOUNT_VALUES, NAF_CODES


apiBlueprint = Blueprint('api', __name__)

OGR_ROME_CODES = load_ogr_rome_mapping()
ROME_CODES = OGR_ROME_CODES.values()

# Some internal services of Pôle emploi can sometimes have access to sensitive information.
API_INTERNAL_CONSUMERS = ['labonneboite', 'memo']


class InvalidFetcherArgument(Exception):
    pass

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

    current_app.logger.debug("API request received: %s", request.full_path)

    try:
        location, zipcode = get_location(request.args)
        fetcher = create_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        message = 'Invalid request argument: {}'.format(e.message)
        return message, 400

    companies, _ = fetcher.get_companies(add_suggestions=False)
    companies_count = fetcher.company_count

    # Define additional query string to add to office urls
    office_query_string = {
        "utm_medium": "web"
    }
    if 'user' in request.args:
        office_query_string['utm_source'] = u'api__{}'.format(request.args['user'])
        office_query_string['utm_campaign'] = u'api__{}'.format(request.args['user'])
        if 'origin_user' in request.args:
            office_query_string['utm_campaign'] += u'__{}'.format(request.args['origin_user'])

    result = {
        'companies': [
            company.as_json(
                rome_code=fetcher.rome, distance=fetcher.distance, zipcode=zipcode,
                extra_query_string=office_query_string
            )
            for company in companies
        ],
        'companies_count': companies_count,
    }

    return jsonify(result)


@apiBlueprint.route('/filter/', methods=['GET'])
@api_auth_required
def company_filter_list():
    current_app.logger.debug("API request received: %s", request.full_path)

    try:
        location, _ = get_location(request.args)
        fetcher = create_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        message = 'Invalid request argument: {}'.format(e.message)
        return message, 400

    # Add aggregations
    fetcher.aggregate_by = search.FILTERS

    _, aggregations = fetcher.get_companies(add_suggestions=False)

    result = {}
    if fetcher.aggregate_by:
        result['filters'] = aggregations

        # If a filter or more are selected, the aggregations returned by fetcher.get_companies()
        # will be filtered too... To avoid that, we are doing additionnal calls (one by filter activated)
        if 'naf_codes' in request.args and 'naf' in fetcher.aggregate_by:
            result['filters']['naf'] = fetcher.get_naf_aggregations()
        if 'headcount' in request.args and 'headcount' in fetcher.aggregate_by:
            result['filters']['headcount'] = fetcher.get_headcount_aggregations()
        if 'contract' in request.args and 'flag_alternance' in fetcher.aggregate_by:
            result['filters']['contract'] = fetcher.get_contract_aggregations()
        if 'distance' in fetcher.aggregate_by and fetcher.distance != search.DISTANCE_FILTER_MAX:
            result['filters']['distance'] = fetcher.get_distance_aggregations()

    return jsonify(result)

def get_location(request_args):
    """
    Parse request arguments to compute location objects.

    Args:
        request_args (dict)

    Return:
        location (Location)
        zipcode (str)
    """
    location = None
    zipcode = None

    # Commune_id or longitude/latitude
    if 'commune_id' in request_args:
        city = geocoding.get_city_by_commune_id(request_args.get('commune_id'))
        if not city:
            raise InvalidFetcherArgument(u'could not resolve latitude and longitude from given commune_id')
        location = search.Location(city['coords']['lat'], city['coords']['lon'])
        zipcode = city['zipcode']
    elif 'latitude' in request_args and 'longitude' in request_args:
        location = search.Location(request_args.get('latitude'), request_args.get('longitude'))
    else:
        raise InvalidFetcherArgument(u'missing arguments: either commune_id or latitude and longitude')

    return location, zipcode


def create_fetcher(location, request_args):
    """
    Returns the filters given a set of parameters.

    Required parameters:
    - `location` (Location)
    - `rome_codes`: one or more "Pôle emploi ROME" codes, comma separated.
    - `commune_id`: "code INSEE" of the city near which to search. If empty `latitude` and `longitude` are required.
    - `latitude` and `longitude`: coordinates of a location near which to search. If empty `commune_id` is required.

    Optional parameters:
    - `distance`: perimeter of the search radius (in Km) in which to search.
    - `page`: number of the requested page.
    - `page_size`: number of results per page (maximum : 100).
    - `naf_codes`: one or more naf_codes, comma separated. If empty or missing, no filter will be used
    - `contract`: one value, only between 'all' (default) or 'alternance'
    - `sort`: one value, only between 'score' (default) and 'distance'
    - `headcount`: one value, only between 'all' (default), 'small' or 'big'
    """
    # Arguments to build the Fetcher object
    kwargs = {}

    # Rome_code
    rome_codes = request_args.get('rome_codes')
    if not rome_codes:
        raise InvalidFetcherArgument(u'missing rome_codes')
    rome_code_list = [code.upper() for code in rome_codes.split(',')]

    for rome in rome_code_list:
        if rome.encode('ascii', 'ignore') not in ROME_CODES:  # ROME_CODES contains ascii data but rome is unicode.
            msg = u'Unknown rome_code: %s - Possible reasons: 1) %s 2) %s' % (
                rome,
                'This rome_code does not exist.',
                'This rome code exists but is very recent and thus \
                    we do not have enough data yet to build relevant results for it. \
                    We typically need at least 12 months of data before we can build \
                    relevant results for a given rome_code.'
            )
            raise InvalidFetcherArgument(msg)

    if len(rome_code_list) > 1:
        # Reasons why we only support single-rome search are detailed in README.md
        raise InvalidFetcherArgument(u'Multi ROME search is no longer supported, please use single ROME search only.')
    kwargs['rome'] = rome_code_list[0]


    # Page and page_size
    try:
        page = int(request_args.get('page'))
    except TypeError:
        page = 1
    try:
        page_size = int(request_args.get('page_size'))
    except TypeError:
        page_size = 10

    if page_size > 100:
        raise InvalidFetcherArgument(u'page_size is too large. Maximum value is 100')

    kwargs['to_number'] = page * page_size
    kwargs['from_number'] = kwargs['to_number'] - page_size + 1

    # Distance
    try:
        distance = int(request_args.get('distance'))
    except (TypeError, ValueError):
        distance = settings.DISTANCE_FILTER_DEFAULT
    kwargs['distance'] = distance

    # Naf
    naf_codes_list = {}
    naf_codes = request_args.get('naf_codes')
    if naf_codes:
        naf_codes_list = [naf.upper() for naf in naf_codes.split(',')]
        invalid_nafs = [naf for naf in naf_codes_list if naf not in NAF_CODES]
        if invalid_nafs:
            raise InvalidFetcherArgument(u'NAF code(s): %s' % ' '.join(invalid_nafs))

        expected_naf_codes = mapping_util.map_romes_to_nafs([kwargs['rome'], ])
        invalid_nafs = [naf for naf in naf_codes_list if naf not in expected_naf_codes]
        if invalid_nafs:
            raise InvalidFetcherArgument(u'NAF code(s): %s. Possible values : %s ' % (
                ' '.join(invalid_nafs), ', '.join(expected_naf_codes)
            ))
    kwargs['naf_codes'] = naf_codes_list


    # Sort
    sort = sorting.SORT_FILTER_DEFAULT
    if 'sort' in request_args:
        sort = request_args.get('sort')
        if sort not in sorting.SORTING_VALUES:
            raise InvalidFetcherArgument(u'sort. Possible values : %s' % ', '.join(sorting.SORTING_VALUES))
    kwargs['sort'] = sort


    # Flag_alternance
    flag_alternance = CONTRACT_VALUES['all']
    if 'contract' in request_args:
        contract = request_args.get('contract')
        if contract not in CONTRACT_VALUES:
            raise InvalidFetcherArgument(u'contract. Possible values : %s' % ', '.join(CONTRACT_VALUES))
        else:
            flag_alternance = CONTRACT_VALUES[contract]
    kwargs['flag_alternance'] = flag_alternance

    # Headcount
    headcount = settings.HEADCOUNT_WHATEVER
    if 'headcount' in request_args:
        headcount = HEADCOUNT_VALUES.get(request_args.get('headcount'))
        if not headcount:
            raise InvalidFetcherArgument(u'headcount. Possible values : %s' % ', '.join(HEADCOUNT_VALUES.keys()))
    kwargs['headcount'] = headcount

    # Departments
    departments = []
    if 'departments' in request_args and request_args.get('departments'):
        departments = request_args.get('departments').split(',')
        unknown_departments = [dep for dep in departments if not geocoding.is_departement(dep)]
        if unknown_departments:
            raise InvalidFetcherArgument(u'departments : %s' % ', '.join(unknown_departments))
    kwargs['departments'] = departments

    return search.Fetcher(location, **kwargs)

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
