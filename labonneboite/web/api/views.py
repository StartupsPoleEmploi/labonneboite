
from functools import wraps

from flask import abort, Blueprint, current_app, jsonify, request, url_for

from labonneboite.common import activity
from labonneboite.common import geocoding
from labonneboite.common import search
from labonneboite.common import offers
from labonneboite.common import sorting
from labonneboite.common import mapping as mapping_util
from labonneboite.common import pagination
from labonneboite.common import hiring_type_util
from labonneboite.common.locations import Location
from labonneboite.common.load_data import ROME_CODES
from labonneboite.common.models import Office
from labonneboite.common.fetcher import InvalidFetcherArgument
from labonneboite.conf import settings
from labonneboite.web.api import util as api_util
from labonneboite.conf.common.settings_common import HEADCOUNT_VALUES
from flask_cors import cross_origin


apiBlueprint = Blueprint('api', __name__)


def api_auth_required(function):
    """
    A decorator that checks that auth and security params are valid.
    This decorator must be used on each view of the API.
    """
    @wraps(function)
    def decorated(*args, **kwargs):
        log_api_request()

        if 'user' not in request.args:
            return 'missing argument: user', 400

        if not current_app.debug:
            try:
                api_util.check_api_request(request)
            except api_util.TimestampFormatException:
                return 'timestamp format: %Y-%m-%dT%H:%M:%S', 400
            except api_util.TimestampExpiredException:
                return 'timestamp has expired', 400
            except api_util.InvalidSignatureException:
                return 'signature is invalid', 400
            except api_util.UnknownUserException:
                return 'user is unknown', 400

        return function(*args, **kwargs)

    return decorated


def get_ga_query_string():
    """
    Define additional Google Analytics query string to add to office urls and global url
    """
    ga_query_string = {"utm_medium": "web"}
    if 'user' in request.args:
        ga_query_string['utm_source'] = 'api__{}'.format(request.args['user'])
        ga_query_string['utm_campaign'] = 'api__{}'.format(request.args['user'])
        if 'origin_user' in request.args:
            ga_query_string['utm_campaign'] += '__{}'.format(request.args['origin_user'])
    return ga_query_string


def log_api_request():
    current_app.logger.debug("API request received: %s", request.full_path)


@apiBlueprint.route('/offers/offices/')
@api_auth_required
def offers_offices_list():

    try:
        fetcher = create_visible_market_fetcher(request.args)
    except InvalidFetcherArgument as e:
        return response_400(e)

    _, zipcode, _ = get_location(request.args)

    offices = fetcher.get_offices()

    result = build_result(fetcher, offices, fetcher.commune_id, zipcode, add_url=False)

    return jsonify(result)


# Note: `company` should be renamed to `office` wherever possible.
# Unfortunately old routes and response formats cannot change due
# to our retrocompatibility standard.


@apiBlueprint.route('/company/')
@api_auth_required
@cross_origin()
def company_list():

    try:
        location, zipcode, commune_id = get_location(request.args)
        fetcher = create_hidden_market_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        return response_400(e)


    offices, _ = fetcher.get_offices(add_suggestions=False)

    result = build_result(fetcher, offices, commune_id, zipcode)

    activity.log_search(
        sirets=[office.siret for office in offices],
        count=fetcher.office_count,
        source='api',
        naf=fetcher.naf_codes,
        localisation={
            'codepostal': zipcode,
            'latitude': location.latitude,
            'longitude': location.longitude,
        },
    )
    return jsonify(result)


@apiBlueprint.route('/company/count/')
@api_auth_required
def company_count():

    try:
        location, _, commune_id = get_location(request.args)
        fetcher = create_hidden_market_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        return response_400(e)

    fetcher.compute_office_count()
    result = get_result(fetcher, commune_id)
    return jsonify(result)


def build_result(fetcher, offices, commune_id, zipcode, add_url=True):
    offices = [
        patch_office_result_with_sensitive_information(request.args['user'], office, office.as_json(
            rome_codes=fetcher.romes,
            distance=fetcher.distance,
            zipcode=zipcode,
            extra_query_string=get_ga_query_string(),
            hiring_type=fetcher.hiring_type,
        ), fetcher.hiring_type == hiring_type_util.ALTERNANCE)
        for office in offices
    ]

    result = get_result(fetcher, commune_id, add_url)
    result['companies'] = offices
    return result


def get_result(fetcher, commune_id=None, add_url=True, add_count=True):
    result = {}
    if len(fetcher.romes) == 1:
        # Showing which rome_code matched at the result level and not the office level
        # only makes sense for single rome search. For multi rome search, the rome_code
        # which matched is added at the office level in office.py:as_json()
        rome_code = fetcher.romes[0]
        result['rome_code'] = rome_code
        result['rome_label'] = settings.ROME_DESCRIPTIONS[rome_code]
    if add_count:
        result['companies_count'] = fetcher.get_office_count()
    if add_url:
        result['url'] = compute_frontend_url(fetcher, get_ga_query_string(), commune_id)
    return result


def compute_frontend_url(fetcher, query_string, commune_id):
    """
    Compute web page URL that corresponds to the API request.
    """

    if not fetcher.office_count >= 1:
        # Always return home URL if zero results
        # (requested by PE.fr)
        return url_for('root.home', _external=True, **query_string)

    if commune_id and fetcher.romes:
        # preserve parameters from original API request
        if fetcher.naf_codes:
            query_string['naf'] = fetcher.naf_codes[0]
        query_string.update({
            'from': fetcher.from_number,
            'to': fetcher.to_number,
            'sort': fetcher.sort,
            'd': fetcher.distance,
            'h': fetcher.headcount,
            'p': fetcher.public,
        })

        return url_for(
            'search.results_by_commune_and_rome',
            commune_id=commune_id,
            # FIXME One day frontend will support multi rome, one day...
            # In the meantime we just provide the URL for the first rome in the list.
            rome_id=fetcher.romes[0],
            _external=True,
            **query_string
        )

    # In case of search by longitude+latitude,
    # return home URL since we do not have a URL ready yet.
    # FIXME implement this URL at some point.
    return url_for('root.home', _external=True, **query_string)


@apiBlueprint.route('/filter/')
@api_auth_required
def company_filter_list():

    try:
        location, _, _ = get_location(request.args)
        fetcher = create_hidden_market_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        return response_400(e)

    # Add aggregations
    fetcher.aggregate_by = search.FILTERS

    _, aggregations = fetcher.get_offices(add_suggestions=False)

    if 'contract' in aggregations:
        raise ValueError("Error, contract aggregation should only be computed at a later step.")

    result = {}
    if fetcher.aggregate_by:
        result['filters'] = aggregations

        # If a filter or more are selected, the aggregations returned by fetcher.get_offices()
        # will be filtered too... To avoid that, we are doing additionnal ES calls (one by filter activated).
        if 'naf_codes' in request.args and 'naf' in fetcher.aggregate_by:
            result['filters']['naf'] = fetcher.get_naf_aggregations()
        if 'headcount' in request.args and 'headcount' in fetcher.aggregate_by:
            result['filters']['headcount'] = fetcher.get_headcount_aggregations()
        if 'distance' in fetcher.aggregate_by and fetcher.distance != search.DISTANCE_FILTER_MAX:
            result['filters']['distance'] = fetcher.get_distance_aggregations()
        if 'hiring_type' in fetcher.aggregate_by:
            result['filters']['contract'] = fetcher.get_contract_aggregations()

    result.update(get_result(fetcher, commune_id=None, add_url=False, add_count=False))

    return jsonify(result)


def response_400(e):
    message = 'Invalid request argument: {}'.format(e.args[0])
    return message, 400


def get_location(request_args):
    """
    Parse request arguments to compute location objects.

    Args:
        request_args (dict)

    Return:
        location (Location)
        zipcode (str)
        commune_id (str)
    """
    location = None
    zipcode = None
    commune_id = None

    # Commune_id or longitude/latitude
    if 'commune_id' in request_args:
        commune_id = request_args['commune_id']
        city = geocoding.get_city_by_commune_id(commune_id)
        if not city:
            raise InvalidFetcherArgument('could not resolve latitude and longitude from given commune_id')
        latitude = city['coords']['lat']
        longitude = city['coords']['lon']
        zipcode = city['zipcode']
    elif 'latitude' in request_args and 'longitude' in request_args:
        if not request_args.get('latitude') or not request_args.get('longitude'):
            raise InvalidFetcherArgument('latitude or longitude (or both) have no value')

        try:
            latitude = float(request_args['latitude'])
            longitude = float(request_args['longitude'])
        except ValueError:
            raise InvalidFetcherArgument('latitude and longitude must be float')
    else:
        raise InvalidFetcherArgument('missing arguments: either commune_id or latitude and longitude')

    location = Location(latitude, longitude)
    return location, zipcode, commune_id


def create_visible_market_fetcher(request_args):
    UNSUPPORTED_PARAMETERS = ['sort', 'naf_codes', 'headcount', 'departments', 'longitude', 'latitude']
    MANDATORY_PARAMETERS = ['rome_codes', 'commune_id', 'contract']

    for param in UNSUPPORTED_PARAMETERS:
        if request_args.get(param):
            raise InvalidFetcherArgument('parameter %s is not supported' % param)

    for param in MANDATORY_PARAMETERS:
        if not request_args.get(param):
            raise InvalidFetcherArgument('parameter %s is required' % param)

    commune_id = request_args.get('commune_id')

    romes = [code.upper() for code in request_args.get('rome_codes').split(',')]
    validate_rome_codes(romes)

    page, page_size = get_page_and_page_size(request_args)
    if page != 1:
        raise InvalidFetcherArgument('only page=1 is supported as pagination is not implemented')

    distance = get_distance(request_args)

    contract = request_args.get('contract')
    if contract == hiring_type_util.CONTRACT_ALTERNANCE:
        hiring_type = hiring_type_util.CONTRACT_TO_HIRING_TYPE[contract]
    else:
        raise InvalidFetcherArgument('only contract=alternance is supported')

    return offers.VisibleMarketFetcher(
        romes=romes,
        commune_id=commune_id,
        distance=distance,
        hiring_type=hiring_type,
        page_size=page_size,
    )


def create_hidden_market_fetcher(location, request_args):
    """
    Returns the filters given a set of parameters.

    Required parameters:
    - `location` (Location): location near which to search.
    - `rome_codes`: one or more "Pôle emploi ROME" codes, comma separated.

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
    - `departments`: one or more departments, comma separated.
    - `flag_pmsmp`: 1 to see only companies having flag_pmsmp=1, all companies otherwise.
    """
    # Arguments to build the HiddenMarketFetcher object
    kwargs = {}

    # Sort
    sort = sorting.SORT_FILTER_DEFAULT
    if 'sort' in request_args:
        sort = request_args.get('sort')
        if sort not in sorting.SORT_FILTERS:
            raise InvalidFetcherArgument('sort. Possible values : %s' % ', '.join(sorting.SORT_FILTERS))
    kwargs['sort'] = sort

    # Rome_code
    rome_codes = request_args.get('rome_codes')
    rome_codes_keyword_search = request_args.get('rome_codes_keyword_search')

    if not rome_codes_keyword_search:
        if not rome_codes:
            raise InvalidFetcherArgument('you must use rome_codes or rome_codes_keyword_search')
    else:
        if rome_codes:
            raise InvalidFetcherArgument('you must either use rome_codes or rome_codes_keyword_search but not both')
        else:
            # ROME keyword search : select first match of what the autocomplete result would be
            suggestions = search.build_job_label_suggestions(rome_codes_keyword_search, size=1)
            if len(suggestions) >= 1:
                rome_codes = suggestions[0]['id']
            else:
                msg = 'No match found for rome_codes_keyword_search.'
                raise InvalidFetcherArgument(msg)

    rome_code_list = [code.upper() for code in rome_codes.split(',')]

    validate_rome_codes(rome_code_list)

    kwargs['romes'] = rome_code_list

    # Page and page_size
    page, page_size = get_page_and_page_size(request_args)
    kwargs['to_number'] = page * page_size
    kwargs['from_number'] = kwargs['to_number'] - page_size + 1

    # Distance
    # WARNING: MAP uses distance=0 in their use of the API.
    kwargs['distance'] = get_distance(request_args)

    # Naf
    naf_codes = {}
    if request_args.get('naf_codes'):
        naf_codes = [naf.upper() for naf in request_args['naf_codes'].split(',')]
        expected_naf_codes = mapping_util.map_romes_to_nafs(kwargs['romes'])
        invalid_nafs = [naf for naf in naf_codes if naf not in expected_naf_codes]
        if invalid_nafs:
            raise InvalidFetcherArgument('NAF code(s): %s. Possible values : %s ' % (
                ' '.join(invalid_nafs), ', '.join(expected_naf_codes)
            ))
    kwargs['naf_codes'] = naf_codes

    # Convert contract to hiring type (DPAE/LBB or Alternance/LBA)
    contract = request_args.get('contract', hiring_type_util.CONTRACT_DEFAULT)
    if contract not in hiring_type_util.CONTRACT_VALUES:
        raise InvalidFetcherArgument('contract. Possible values : %s' % ', '.join(hiring_type_util.CONTRACT_VALUES))
    kwargs['hiring_type'] = hiring_type_util.CONTRACT_TO_HIRING_TYPE[contract]

    # Headcount
    headcount = settings.HEADCOUNT_WHATEVER
    if 'headcount' in request_args:
        headcount = HEADCOUNT_VALUES.get(request_args.get('headcount'))
        if not headcount:
            raise InvalidFetcherArgument('headcount. Possible values : %s' % ', '.join(sorted(HEADCOUNT_VALUES.keys())))
    kwargs['headcount'] = headcount

    # Departments
    departments = []
    if 'departments' in request_args and request_args.get('departments'):
        departments = request_args.get('departments').split(',')
        unknown_departments = [dep for dep in departments if not geocoding.is_departement(dep)]
        if unknown_departments:
            raise InvalidFetcherArgument('departments : %s' % ', '.join(unknown_departments))
    kwargs['departments'] = departments

    # PMSMP filter only available for internal users.
    if request.args['user'] in settings.API_INTERNAL_CONSUMERS:
        kwargs['flag_pmsmp'] = check_bool_argument(request_args, 'flag_pmsmp', 0)

    return search.HiddenMarketFetcher(location, **kwargs)


def check_bool_argument(args, name, default_value):
    """
    Return value from arguments, check that value is boolean.

    Args:
        args (dict)
        name (str)
        default_value (int)
    """
    value = args.get(name, default_value)
    try:
        value = int(value)
        if value not in [0, 1]:
            raise ValueError
    except (TypeError, ValueError):
        raise InvalidFetcherArgument('{} must be boolean (0 or 1)'.format(name))
    return value


def get_distance(request_args):
    return check_integer_argument(request_args, 'distance', settings.DISTANCE_FILTER_DEFAULT)


def get_page_and_page_size(request_args):
    page = check_positive_integer_argument(request_args, 'page', 1)
    page_size = check_positive_integer_argument(request_args, 'page_size', pagination.OFFICES_PER_PAGE)
    if page_size > pagination.OFFICES_MAXIMUM_PAGE_SIZE:
        raise InvalidFetcherArgument(
            'page_size is too large. Maximum value is %s' % pagination.OFFICES_MAXIMUM_PAGE_SIZE
        )
    return page, page_size


def validate_rome_codes(rome_code_list):
    for rome in rome_code_list:
        if rome not in ROME_CODES:  # ROME_CODES contains ascii data but rome is unicode.
            msg = 'Unknown rome_code: %s - Possible reasons: 1) %s 2) %s' % (
                rome,
                'This rome_code does not exist.',
                'This rome code exists but is very recent and thus \
                    we do not have enough data yet to build relevant results for it. \
                    We typically need at least 12 months of data before we can build \
                    relevant results for a given rome_code.'
            )
            raise InvalidFetcherArgument(msg)
    if len(rome_code_list) == 0:
        raise InvalidFetcherArgument("At least one rome_code is required.")


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
        raise InvalidFetcherArgument('{} must be positive'.format(name))
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
        raise InvalidFetcherArgument('{} must be integer'.format(name))
    return value


@apiBlueprint.route('/office/<siret>/details')
@api_auth_required
def office_details(siret):
    """
    Returns the details of an office for the given <siret> number.
    """
    alternance = 'contract' in request.args and request.args['contract'] == 'alternance'
    return get_office_details(siret, alternance)


def get_office_details(siret, alternance=False):
    office = Office.query.filter_by(siret=siret).first()
    if not office:
        abort(404)

    # If an office score equals 0 it means it is not supposed
    # to be shown on LBB frontend/api
    # and/or it was specifically removed via SAVE,
    # and thus it should not be accessible by siret.
    if not alternance and not office.score:
        abort(404)

    # Offices having score_alternance equal 0 may still be accessed
    # by siret in case of LBA offices from the visible market (i.e. having
    # at least one job offer obtained from the API Offers V2).
    # However we should not show them if they were specifically removed via SAVE.
    if alternance and office.is_removed_from_lba:
        abort(404)

    # If alternance flag, we use an other URL
    url = office.url_alternance if alternance else office.url

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
        'url': url,
        'social_network': office.social_network or '',
        'address': {
            'city': office.city,
            'city_code': office.city_code,
            'street_name': office.street_name,
            'street_number': office.street_number,
            'zipcode': office.zipcode,
        },
    }
    patch_office_result_with_sensitive_information(request.args['user'], office, result, alternance)
    return jsonify(result)


def patch_office_result_with_sensitive_information(api_username, office, result, alternance=False):
    # Some internal services of Pôle emploi can sometimes have access to
    # sensitive information.
    if api_username in settings.API_INTERNAL_CONSUMERS:
        result['email'] = office.email_alternance if alternance and office.email_alternance else office.email
        result['phone'] = office.phone_alternance if alternance and office.phone_alternance else office.tel
        result['website'] = office.website_alternance if alternance and office.website_alternance else office.website
    return result
