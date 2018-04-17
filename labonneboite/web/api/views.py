# coding: utf8

from functools import wraps

from flask import abort, Blueprint, current_app, jsonify, request

from labonneboite.common import geocoding
from labonneboite.common import search
from labonneboite.common import sorting
from labonneboite.common import mapping as mapping_util
from labonneboite.common import pagination
from labonneboite.common import hiring_type_util
from labonneboite.common.load_data import load_ogr_rome_mapping
from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.web.api import util as api_util
from labonneboite.conf.common.settings_common import CONTRACT_VALUES, HEADCOUNT_VALUES, NAF_CODES


apiBlueprint = Blueprint('api', __name__)

OGR_ROME_CODES = load_ogr_rome_mapping()
ROME_CODES = OGR_ROME_CODES.values()


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


def get_ga_query_string():
    """
    Define additional Google Analytics query string to add to office urls and global url
    """
    ga_query_string = {"utm_medium": "web"}
    if 'user' in request.args:
        ga_query_string['utm_source'] = u'api__{}'.format(request.args['user'])
        ga_query_string['utm_campaign'] = u'api__{}'.format(request.args['user'])
        if 'origin_user' in request.args:
            ga_query_string['utm_campaign'] += u'__{}'.format(request.args['origin_user'])
    return ga_query_string


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

    ga_query_string = get_ga_query_string()

    companies, _ = fetcher.get_companies(add_suggestions=False)
    companies_count = fetcher.company_count
    url = fetcher.compute_url(ga_query_string)

    companies = [
        patch_company_result(request.args['user'], company, company.as_json(
            rome_code=fetcher.rome, distance=fetcher.distance, zipcode=zipcode,
            extra_query_string=ga_query_string,
        ))
        for company in companies
    ]

    result = {
        'companies': companies,
        'companies_count': companies_count,
        'url': url,
        'rome_code': fetcher.rome,
        'rome_label': settings.ROME_DESCRIPTIONS[fetcher.rome],
    }

    return jsonify(result)


@apiBlueprint.route('/company/count/', methods=['GET'])
@api_auth_required
def company_count():

    current_app.logger.debug("API request received: %s", request.full_path)

    try:
        location, _ = get_location(request.args)
        fetcher = create_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        message = 'Invalid request argument: {}'.format(e.message)
        return message, 400

    ga_query_string = get_ga_query_string()

    fetcher.compute_company_count()
    companies_count = fetcher.company_count
    url = fetcher.compute_url(ga_query_string)

    result = {
        'companies_count': companies_count,
        'url': url,
        'rome_code': fetcher.rome,
        'rome_label': settings.ROME_DESCRIPTIONS[fetcher.rome],
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

    result.update({
        'rome_code': fetcher.rome,
        'rome_label': settings.ROME_DESCRIPTIONS[fetcher.rome],
    })

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
        location = search.Location(city['coords']['lat'], city['coords']['lon'], request_args.get('commune_id'))
        zipcode = city['zipcode']
    elif 'latitude' in request_args and 'longitude' in request_args:
        if not request_args.get('latitude') or not request_args.get('longitude'):
            raise InvalidFetcherArgument(u'latitude or longitude (or both) have no value')

        try:
            latitude = float(request_args['latitude'])
            longitude = float(request_args['longitude'])
        except ValueError:
            raise InvalidFetcherArgument(u'latitude or longitude (or both) must be float')

        location = search.Location(latitude, longitude)

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
    - `page_size`: number of results per page (
        maximum : pagination.OFFICES_MAXIMUM_PAGE_SIZE,
        default: pagination.OFFICES_PER_PAGE
        ).
    - `naf_codes`: one or more naf_codes, comma separated. If empty or missing, no filter will be used
    - `contract`: one value, only between 'all' (default) or 'alternance'
    - `sort`: one value, only between 'score' (default) and 'distance'
    - `headcount`: one value, only between 'all' (default), 'small' or 'big'
    """
    # Arguments to build the Fetcher object
    kwargs = {}

    # Rome_code
    rome_codes = request_args.get('rome_codes')
    rome_codes_keyword_search = request_args.get('rome_codes_keyword_search')

    if not rome_codes_keyword_search:
        if not rome_codes:
            raise InvalidFetcherArgument(u'you must use rome_codes or rome_codes_keyword_search')
    else:
        if rome_codes:
            raise InvalidFetcherArgument(u'you must either use rome_codes or rome_codes_keyword_search but not both')
        else:
            # ROME keyword search : select first match of what the autocomplete result would be
            suggestions = search.build_job_label_suggestions(rome_codes_keyword_search, size=1)
            if len(suggestions) >= 1:
                rome_codes = suggestions[0]['id']
            else:
                msg = u'No match found for rome_codes_keyword_search.'
                raise InvalidFetcherArgument(msg)

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
        raise InvalidFetcherArgument(
            u'Multi ROME search is not supported at the moment, please use single ROME search only.')
    kwargs['rome'] = rome_code_list[0]

    # Page and page_size
    page = check_positive_integer_argument(request_args, 'page', 1)
    page_size = check_positive_integer_argument(request_args, 'page_size', pagination.OFFICES_PER_PAGE)
    if page_size > pagination.OFFICES_MAXIMUM_PAGE_SIZE:
        raise InvalidFetcherArgument(
            u'page_size is too large. Maximum value is %s' % pagination.OFFICES_MAXIMUM_PAGE_SIZE
        )

    kwargs['to_number'] = page * page_size
    kwargs['from_number'] = kwargs['to_number'] - page_size + 1

    # Distance
    # WARNING: MAP uses distance=0 in their use of the API.
    kwargs['distance'] = check_integer_argument(request_args, 'distance', settings.DISTANCE_FILTER_DEFAULT)

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

    # Hiring type (DPAE/LBB or Alternance/LBA)
    hiring_type = request_args.get('hiring_type', hiring_type_util.DEFAULT)
    if hiring_type not in hiring_type_util.VALUES:
        raise InvalidFetcherArgument(u'hiring_type. Possible values : %s' % ', '.join(hiring_type_util.VALUES))
    kwargs['hiring_type'] = hiring_type

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


def check_positive_integer_argument(args, name, default_value):
    """
    Return value from arguments, check that value is integer and positive.

    Args:
        args (dict)
        name (str)
        default_value (int)
    """
    value = check_integer_argument(args, name, default_value)
    if value <= 0:
        raise InvalidFetcherArgument(u'{} must be positive'.format(name))
    return value


def check_integer_argument(args, name, default_value):
    """
    Return value from arguments, check that value is integer.

    Args:
        args (dict)
        name (str)
        default_value (int)
    """
    value = args.get(name, default_value)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise InvalidFetcherArgument(u'{} must be integer'.format(name))
    return value


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
        'raison_sociale': office.company_name,
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
    patch_company_result(request.args['user'], office, result)
    return jsonify(result)


def patch_company_result(api_username, office, result):
    # Some internal services of Pôle emploi can sometimes have access to
    # sensitive information.
    if api_username in settings.API_INTERNAL_CONSUMERS:
        result['email'] = office.email
        result['phone'] = office.tel
        result['website'] = office.website
    return result
