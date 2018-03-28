# coding: utf8

from urllib import urlencode
import json

from slugify import slugify

from flask import abort, make_response, redirect, render_template, request, session, url_for
from flask import Blueprint
from flask_login import current_user

from labonneboite.common import geocoding
from labonneboite.common import doorbell
from labonneboite.common import pro
from labonneboite.common import sorting
from labonneboite.common import search as search_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common import pagination
from labonneboite.common.models import UserFavoriteOffice

from labonneboite.conf import settings
from labonneboite.web.search.forms import CompanySearchForm


searchBlueprint = Blueprint('search', __name__)


@searchBlueprint.route('/suggest_job_labels', methods=['GET'])
def suggest_job_labels():
    term = request.args.get('term', '')
    suggestions = search_util.build_job_label_suggestions(term)
    return make_response(json.dumps(suggestions))


@searchBlueprint.route('/suggest_locations', methods=['GET'])
def suggest_locations():
    term = request.args.get('term', '')
    suggestions = search_util.build_location_suggestions(term)
    return make_response(json.dumps(suggestions))

@searchBlueprint.route('/job_slug_details')
def job_slug_details():
    result = []

    job_slug = request.args.get('job-slug', '')
    if not job_slug:
        return u'no job-slug given', 400

    slugs = job_slug.split(',')
    for slug in slugs:
        rome = mapping_util.SLUGIFIED_ROME_LABELS.get(slug)
        # Ignored unknown job slugs
        if rome:
            result.append({
                'rome_code': rome,
                'label': settings.ROME_DESCRIPTIONS.get(rome, ''),
            })

    return make_response(json.dumps(result))


@searchBlueprint.route('/city_slug_details')
def city_slug_details():
    result = {}

    city_slug = request.args.get('city-slug', '')
    if not city_slug:
        return u'no city-slug given', 400

    city = city_slug.split('-')
    zipcode = ''.join(city[-1:])
    city_temp = search_util.CityLocation(city_slug, zipcode)

    if not city_temp or not city_temp.location:
        return u'no city found associated to the slug {}'.format(city_slug), 400

    # Name without zipcode
    name = city_temp.name.replace(zipcode, '').strip()

    result['city'] = {
        'name': name,
        'longitude': city_temp.location.longitude,
        'latitude': city_temp.location.latitude,
    }

    return make_response(json.dumps(result))


@searchBlueprint.route('/recherche')
def recherche():
    form = CompanySearchForm(request.args)
    if request.args and form.validate():
        return form.redirect('search.results')
    return render_template('search/results.html', form=form)


PARAMETER_FIELD_MAPPING = {
    'j': 'job',
    'r': 'rome',
    'q': 'job',
    'lat': 'latitude',
    'lon': 'longitude',
    'd': 'distance',
    'l': 'location',
    'h': 'headcount',
    'mode': 'mode',
    'naf': 'naf',
    'sort': 'sort',
    'from': 'from_number',
    'to': 'to_number',
    'f_a': 'flag_alternance',
    'p': 'public',
}


def get_parameters(args):
    kwargs = {}

    for param, field_name in PARAMETER_FIELD_MAPPING.iteritems():
        kwargs[field_name] = args.get(param, '')

    try:
        kwargs['distance'] = int(kwargs.get('distance'))
    except ValueError:
        kwargs['distance'] = settings.DISTANCE_FILTER_DEFAULT

    try:
        kwargs['headcount'] = int(kwargs.get('headcount'))
    except ValueError:
        kwargs['headcount'] = settings.HEADCOUNT_FILTER_DEFAULT

    try:
        kwargs['from_number'] = int(kwargs.get('from_number'))
    except ValueError:
        kwargs['from_number'] = 1

    try:
        kwargs['to_number'] = int(kwargs.get('to_number'))
    except ValueError:
        kwargs['to_number'] = kwargs['from_number'] + pagination.OFFICES_PER_PAGE - 1

    # Fix pagination when needed
    if not kwargs['from_number'] >= 1:
        kwargs['from_number'] = 1
    current_page_size = kwargs['to_number'] - kwargs['from_number'] + 1
    if current_page_size <= 0:  # this may happen when a 'out of bound' page is requested
        kwargs['to_number'] = kwargs['from_number'] + pagination.OFFICES_PER_PAGE - 1
    if current_page_size > pagination.OFFICES_MAXIMUM_PAGE_SIZE:
        kwargs['to_number'] = kwargs['from_number'] + pagination.OFFICES_MAXIMUM_PAGE_SIZE - 1

    # Fallback to default sorting.
    if kwargs.get('sort') not in sorting.SORT_FILTERS:
        kwargs['sort'] = sorting.SORT_FILTER_DEFAULT

    for flag_name in ['flag_alternance', 'public']:
        try:
            kwargs[flag_name] = int(kwargs.get(flag_name))
        except (ValueError, TypeError):
            kwargs[flag_name] = 0

    kwargs['flag_alternance'] = 0  # FIXME drop flag_alternance forever
    
    if kwargs['public'] not in search_util.PUBLIC_CHOICES:
        kwargs['public'] = search_util.PUBLIC_ALL

    # ensure PRO filters are never used in the public version
    if not pro.pro_version_enabled():
        del kwargs['public']

    return kwargs


@searchBlueprint.route('/entreprises/<city>-<zipcode>/<occupation>')
def results(city, zipcode, occupation):

    canonical = url_for('search.results', city=city, zipcode=zipcode, occupation=occupation)
    city = search_util.CityLocation(city, zipcode)
    session['search_args'] = request.args
    parameters = get_parameters(request.args)
    rome = mapping_util.SLUGIFIED_ROME_LABELS.get(occupation)

    # Remove keys with empty values to build form
    form_kwargs = {key: val for key, val in parameters.items() if val}
    form_kwargs['occupation'] = occupation
    form_kwargs['location'] = city.full_name
    form_kwargs['city'] = city.slug
    form_kwargs['zipcode'] = city.zipcode
    form_kwargs['job'] = settings.ROME_DESCRIPTIONS.get(rome, occupation)
    form = CompanySearchForm(**form_kwargs)

    # Get ROME code (Répertoire Opérationnel des Métiers et des Emplois).
    # and stop here if the ROME code does not exists.
    if not rome:
        return render_template('search/results.html', job_doesnt_exist=True, form=form)

    # Fetch companies and alternatives
    fetcher = search_util.Fetcher(
        city.location,
        rome=rome,
        distance=parameters['distance'],
        sort=parameters['sort'],
        from_number=parameters['from_number'],
        to_number=parameters['to_number'],
        flag_alternance=parameters['flag_alternance'],
        public=parameters.get('public'),
        headcount=parameters['headcount'],
        naf=parameters['naf'],
        naf_codes=None,
        aggregate_by=['naf'],
        departments=None,
    )
    alternative_rome_descriptions = []
    naf_codes_with_descriptions = []
    companies = []
    company_count = 0
    alternative_distances = {}

    if city.is_location_correct:
        companies, aggregations = fetcher.get_companies(add_suggestions=True)
        company_count = fetcher.company_count
        alternative_distances = fetcher.alternative_distances
        alternative_rome_descriptions = fetcher.get_alternative_rome_descriptions()

        # If a filter or more are selected, the aggregations returned by fetcher.get_companies()
        # will be filtered too... To avoid that, we are doing additionnal calls (one by filter activated)
        if aggregations:
            fetcher.update_aggregations(aggregations)

        # Generates values for the NAF filter
        # aggregations could be empty if errors or empty results
        if aggregations:
            for naf_aggregate in aggregations['naf']:
                naf_description = '%s (%s)' % (settings.NAF_CODES.get(naf_aggregate["code"]), naf_aggregate["count"])
                naf_codes_with_descriptions.append((naf_aggregate["code"], naf_description))

    # Pagination.
    pagination_manager = pagination.PaginationManager(
        company_count,
        fetcher.from_number,
        fetcher.to_number,
        request.full_path,
    )
    current_page = pagination_manager.get_current_page()

    form.naf.choices = [('', u'Tous les secteurs')] + sorted(naf_codes_with_descriptions, key=lambda t: t[1])
    form.validate()

    context = {
        'alternative_distances': alternative_distances,
        'alternative_rome_descriptions': alternative_rome_descriptions,
        'canonical': canonical,
        'city': city,
        'companies': list(companies),
        'companies_per_page': pagination.OFFICES_PER_PAGE,
        'company_count': company_count,
        'distance': fetcher.distance,
        'doorbell_tags': doorbell.get_tags('results'),
        'form': form,
        'headcount': fetcher.headcount,
        'job_doesnt_exist': False,
        'naf': fetcher.naf,
        'page': current_page,
        'pagination': pagination_manager,
        'rome_code': fetcher.rome,
        'rome_description': settings.ROME_DESCRIPTIONS.get(fetcher.rome, ''),
        'show_favorites': True,
        'sort': fetcher.sort,
        'tile_server_url': settings.TILE_SERVER_URL,
        'user_favs_as_sirets': UserFavoriteOffice.user_favs_as_sirets(current_user),
    }
    return render_template('search/results.html', **context)


@searchBlueprint.route('/entreprises/commune/<commune_id>/rome/<rome_id>', methods=['GET'])
def results_by_commune_and_rome(commune_id, rome_id):
    """
    Convenience function to be used by Pôle Emploi, Bob Emploi and other partners
    Redirects internally to our real user-facing url displaying
    results for his search.

    For more information about the differences between commune_id and zipcode,
    please consult README file
    """
    try:
        rome_description = settings.ROME_DESCRIPTIONS[rome_id.upper()]
        slugified_rome_description = slugify(rome_description)
    except KeyError:
        rome_description = None
    city = geocoding.get_city_by_commune_id(commune_id)

    if not city or not rome_description:
        abort(404)

    url = url_for('search.results', city=city['slug'], zipcode=city['zipcode'], occupation=slugified_rome_description)
    # Pass all GET params to the redirect URL: this will allow users of the API to build web links
    # roughly equivalent to the result of an API call - see Trello #971.
    return redirect('%s?%s' % (url, urlencode(request.args)))
