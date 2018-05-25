# coding: utf8

from functools import wraps

from flask import abort, Blueprint, current_app, jsonify, request, url_for

from labonneboite.common import geocoding
from labonneboite.common import search
from labonneboite.common import sorting
from labonneboite.common import mapping as mapping_util
from labonneboite.common import pagination
from labonneboite.common import hiring_type_util
from labonneboite.common.locations import Location
from labonneboite.common.load_data import load_ogr_rome_mapping
from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.web.api import util as api_util
from labonneboite.conf.common.settings_common import HEADCOUNT_VALUES, NAF_CODES


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
        location, zipcode, commune_id = get_location(request.args)
        fetcher = create_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        message = 'Invalid request argument: {}'.format(e.message)
        return message, 400

    companies, _ = fetcher.get_companies(add_suggestions=False)

    companies = [
        patch_company_result_with_sensitive_information(request.args['user'], company, company.as_json(
            rome_codes=fetcher.romes,
            distance=fetcher.distance,
            zipcode=zipcode,
            extra_query_string=get_ga_query_string(),
            hiring_type=fetcher.hiring_type,
        ))
        for company in companies
    ]

    result = get_result(fetcher, commune_id)
    result['companies'] = companies
    return jsonify(result)


@apiBlueprint.route('/company/count/', methods=['GET'])
@api_auth_required
def company_count():

    current_app.logger.debug("API request received: %s", request.full_path)

    try:
        location, _, commune_id = get_location(request.args)
        fetcher = create_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        message = 'Invalid request argument: {}'.format(e.message)
        return message, 400

    fetcher.compute_company_count()
    result = get_result(fetcher, commune_id)
    return jsonify(result)


def get_result(fetcher, commune_id=None, add_url=True, add_count=True):
    result = {}
    if len(fetcher.romes) == 1:
        # Showing which rome_code matched at the result level and not the company level
        # only makes sense for single rome search. For multi rome search, the rome_code
        # which matched is added at the company level in office.py:as_json()
        rome_code = fetcher.romes[0]
        result['rome_code'] = rome_code
        result['rome_label'] = settings.ROME_DESCRIPTIONS[rome_code]
    if add_count:
        result['companies_count'] = fetcher.company_count
    if add_url:
        result['url'] = compute_frontend_url(fetcher, get_ga_query_string(), commune_id)
    return result


def compute_frontend_url(fetcher, query_string, commune_id):
    """
    Compute web page URL that corresponds to the API request.
    """

    if not fetcher.company_count >= 1:
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


@apiBlueprint.route('/filter/', methods=['GET'])
@api_auth_required
def company_filter_list():
    current_app.logger.debug("API request received: %s", request.full_path)

    try:
        location, _, _ = get_location(request.args)
        fetcher = create_fetcher(location, request.args)
    except InvalidFetcherArgument as e:
        message = 'Invalid request argument: {}'.format(e.message)
        return message, 400

    # Add aggregations
    fetcher.aggregate_by = search.FILTERS

    _, aggregations = fetcher.get_companies(add_suggestions=False)

    if 'contract' in aggregations:
        raise ValueError("Error, contract aggregation should only be computed at a later step.")

    result = {}
    if fetcher.aggregate_by:
        result['filters'] = aggregations

        # If a filter or more are selected, the aggregations returned by fetcher.get_companies()
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
    commune_id = None

    # Commune_id or longitude/latitude
    if 'commune_id' in request_args:
        commune_id = request_args['commune_id']
        city = geocoding.get_city_by_commune_id(commune_id)
        if not city:
            raise InvalidFetcherArgument(u'could not resolve latitude and longitude from given commune_id')
        latitude = city['coords']['lat']
        longitude = city['coords']['lon']
        zipcode = city['zipcode']
    elif 'latitude' in request_args and 'longitude' in request_args:
        if not request_args.get('latitude') or not request_args.get('longitude'):
            raise InvalidFetcherArgument(u'latitude or longitude (or both) have no value')

        try:
            latitude = float(request_args['latitude'])
            longitude = float(request_args['longitude'])
        except ValueError:
            raise InvalidFetcherArgument(u'latitude and longitude must be float')
    else:
        raise InvalidFetcherArgument(u'missing arguments: either commune_id or latitude and longitude')

    location = Location(latitude, longitude)
    return location, zipcode, commune_id


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

    # Sort
    sort = sorting.SORT_FILTER_DEFAULT
    if 'sort' in request_args:
        sort = request_args.get('sort')
        if sort not in sorting.SORT_FILTERS:
            raise InvalidFetcherArgument(u'sort. Possible values : %s' % ', '.join(sorting.SORT_FILTERS))
    kwargs['sort'] = sort

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

    kwargs['romes'] = rome_code_list

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
    naf_codes = {}
    if request_args.get('naf_codes'):
        naf_codes = [naf.upper() for naf in request_args['naf_codes'].split(',')]
        expected_naf_codes = mapping_util.map_romes_to_nafs(kwargs['romes'])
        invalid_nafs = [naf for naf in naf_codes if naf not in expected_naf_codes]
        if invalid_nafs:
            raise InvalidFetcherArgument(u'NAF code(s): %s. Possible values : %s ' % (
                ' '.join(invalid_nafs), ', '.join(expected_naf_codes)
            ))
    kwargs['naf_codes'] = naf_codes

    # Convert contract to hiring type (DPAE/LBB or Alternance/LBA)
    contract = request_args.get('contract', hiring_type_util.CONTRACT_DEFAULT)
    if contract not in hiring_type_util.CONTRACT_VALUES:
        raise InvalidFetcherArgument(u'contract. Possible values : %s' % ', '.join(hiring_type_util.CONTRACT_VALUES))
    kwargs['hiring_type'] = hiring_type_util.CONTRACT_TO_HIRING_TYPE[contract]

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


@apiBlueprint.route('/office/<siret>/details')
@api_auth_required
def office_details_lbb(siret):
    """
    Returns the details of an office for the given <siret> number.
    """
    return get_office_details(siret)


@apiBlueprint.route('/office/<siret>/details-alternance')
@api_auth_required
def office_details_alternance(siret):
    """
    Returns the details of an office for the given <siret> number (with alternance infos).
    """
    return get_office_details(siret, alternance=True)


def get_office_details(siret, alternance=False):
    office = Office.query.filter_by(siret=siret).first()
    if not office:
        abort(404)

    # If a office.score_alternance=0 (meaning removed for alternance),
    # it should not be accessible by siret on alternance context
    if alternance and not office.score_alternance:
        abort(404)

    # If a office.score=0 (meaning removed),
    # it should not be accessible by siret
    if not alternance and not office.score:
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
        'address': {
            'city': office.city,
            'city_code': office.city_code,
            'street_name': office.street_name,
            'street_number': office.street_number,
            'zipcode': office.zipcode,
        },
    }
    patch_company_result_with_sensitive_information(request.args['user'], office, result, alternance)
    return jsonify(result)


def patch_company_result_with_sensitive_information(api_username, office, result, alternance=False):
    # Some internal services of Pôle emploi can sometimes have access to
    # sensitive information.
    if api_username in settings.API_INTERNAL_CONSUMERS:
        result['email'] = office.email_alternance if alternance and office.email_alternance else office.email
        result['phone'] = office.tel
        result['website'] = office.website
    return result
