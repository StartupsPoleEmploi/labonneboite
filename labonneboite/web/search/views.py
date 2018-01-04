# coding: utf8

from urllib import urlencode
import json

from slugify import slugify

from flask import abort, make_response, redirect, render_template, request, session, url_for
from flask import Blueprint, current_app
from flask_login import current_user

from labonneboite.common import geocoding
from labonneboite.common import doorbell
from labonneboite.common import pro
from labonneboite.common import util
from labonneboite.common import sorting
from labonneboite.common import search as search_util
from labonneboite.common import mapping as mapping_util
from labonneboite.common.models import UserFavoriteOffice

from labonneboite.conf import settings
from labonneboite.web.pagination import PaginationManager
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


@searchBlueprint.route('/recherche')
def search():
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
        kwargs['to_number'] = kwargs['from_number'] + settings.PAGINATION_COMPANIES_PER_PAGE - 1

    if kwargs.get('sort') == '':
        kwargs['sort'] = sorting.SORT_FILTER_DEFAULT

    for flag_name in ['flag_alternance', 'public']:
        try:
            kwargs[flag_name] = int(kwargs.get(flag_name))
        except (ValueError, TypeError):
            kwargs[flag_name] = 0

    if kwargs['flag_alternance'] not in [0, 1]:
        kwargs['flag_alternance'] = 0
    if kwargs['public'] not in search_util.PUBLIC_CHOICES:
        kwargs['public'] = search_util.PUBLIC_ALL

    # ensure PRO filters are never used in the public version
    if not pro.pro_version_enabled():
        del kwargs['public']

    return kwargs


@searchBlueprint.route('/entreprises/<city>-<zipcode>/<occupation>')
def results(city, zipcode, occupation):

    canonical = '/entreprises/%s-%s/%s' % (city, zipcode, occupation)
    city = search_util.CityLocation(city, zipcode)

    kwargs = get_parameters(request.args)
    kwargs['occupation'] = occupation

    # Remove keys with empty values.
    form_kwargs = {key: val for key, val in kwargs.items() if val}
    form_kwargs['location'] = city.full_name
    form_kwargs['city'] = city.slug
    form_kwargs['zipcode'] = city.zipcode

    # Get ROME code (Répertoire Opérationnel des Métiers et des Emplois).
    rome = mapping_util.SLUGIFIED_ROME_LABELS.get(occupation)

    # Stop here if the ROME code does not exists.
    if not rome:
        form_kwargs['job'] = occupation
        form = CompanySearchForm(**form_kwargs)
        return render_template('search/results.html', job_doesnt_exist=True, form=form)

    session['search_args'] = request.args

    # Fetch companies and alternatives
    kwargs['rome'] = rome
    kwargs['aggregate_by'] = ['naf']

    fetcher = search_util.Fetcher(city.location, **kwargs)
    alternative_rome_descriptions = []
    naf_codes_with_descriptions = []

    if not city.is_location_correct:
        companies = []
        aggregations = []
        company_count = 0
        alternative_distances = {}
    else:
        current_app.logger.debug("fetching companies and company_count")

        companies, aggregations = fetcher.get_companies(add_suggestions=True)
        for alternative, count in fetcher.alternative_rome_codes.iteritems():
            if settings.ROME_DESCRIPTIONS.get(alternative) and count:
                desc = settings.ROME_DESCRIPTIONS.get(alternative)
                slug = slugify(desc)
                alternative_rome_descriptions.append([alternative, desc, slug, count])
        company_count = fetcher.company_count
        alternative_distances = fetcher.alternative_distances

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
    pagination_manager = PaginationManager(company_count, fetcher.from_number, fetcher.to_number, request.full_path)
    current_page = pagination_manager.get_current_page()

    # Get contact mode and position.
    for position, company in enumerate(companies, start=1):
        company.contact_mode = util.get_contact_mode_for_rome_and_naf(fetcher.rome, company.naf)
        # position is later used in labonneboite/web/static/js/results.js
        company.position = position

    form_kwargs['job'] = settings.ROME_DESCRIPTIONS[rome]
    form = CompanySearchForm(**form_kwargs)
    form.naf.choices = [('', u'Tous les secteurs')] + sorted(naf_codes_with_descriptions, key=lambda t: t[1])
    form.validate()

    context = {
        'alternative_distances': alternative_distances,
        'alternative_rome_descriptions': alternative_rome_descriptions,
        'canonical': canonical,
        'city': city,
        'companies': list(companies),
        'company_count': company_count,
        'distance': fetcher.distance,
        'doorbell_tags': doorbell.get_tags('results'),
        'form': form,
        'headcount': fetcher.headcount,
        'job_doesnt_exist': False,
        'naf': fetcher.naf,
        'naf_codes': naf_codes_with_descriptions,
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
    Convenience function to be used by Bob Emploi and other partners
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
        msg = '[404] /entreprises/commune/%s/rome/%s : rome_description=%s' % (commune_id, rome_id, rome_description)
        current_app.logger.error(msg)
        abort(404)

    url = url_for('search.results', city=city['slug'], zipcode=city['zipcode'], occupation=slugified_rome_description)
    # Pass all GET params to the redirect URL: this will allow users of the API to build web links
    # roughly equivalent to the result of an API call - see Trello #971.
    return redirect('%s?%s' % (url, urlencode(request.args)))
