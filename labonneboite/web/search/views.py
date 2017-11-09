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
    'from': 'from',
    'to': 'to',
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
        kwargs['from'] = int(kwargs.get('from'))
    except ValueError:
        kwargs['from'] = 1

    try:
        kwargs['to'] = int(kwargs.get('to'))
    except ValueError:
        kwargs['to'] = kwargs['from'] + settings.PAGINATION_COMPANIES_PER_PAGE - 1

    if kwargs.get('sort') == '':
        kwargs['sort'] = settings.SORT_FILTER_DEFAULT

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

    kwargs = get_parameters(request.args)
    kwargs['city'] = city
    kwargs['zipcode'] = zipcode
    kwargs['occupation'] = occupation

    canonical = '/entreprises/%s-%s/%s' % (city, zipcode, occupation)

    # Remove keys with empty values.
    form_kwargs = {key: val for key, val in dict(**kwargs).items() if val}

    city = city.replace('-', ' ').capitalize()
    full_location = '%s (%s)' % (city, zipcode)
    form_kwargs['location'] = full_location

    # Get ROME code (Répertoire Opérationnel des Métiers et des Emplois).
    rome = mapping_util.SLUGIFIED_ROME_LABELS.get(occupation)

    # Stop here if the ROME code does not exists.
    if not rome:
        form_kwargs['job'] = occupation
        form = CompanySearchForm(**form_kwargs)
        context = {'job_doesnt_exist': True, 'form': form}
        return render_template('search/results.html', **context)

    session['search_args'] = request.args

    # Fetch companies and alternatives.
    fetcher = search_util.Fetcher(**kwargs)
    alternative_rome_descriptions = []
    alternative_distances = {}
    companies = []
    naf_aggregations = []
    company_count = 0

    try:
        fetcher.init_location()
        zipcode_is_invalid = False
    except search_util.InvalidZipcodeError:
        zipcode_is_invalid = True

    if not zipcode_is_invalid:
        current_app.logger.debug("fetching companies and company_count")
        # Note that if a NAF filter is selected, naf_aggregations will be a list of
        # only one NAF, the one currently selected in the filter.
        companies, naf_aggregations = fetcher.get_companies()
        for alternative, count in fetcher.alternative_rome_codes.iteritems():
            if settings.ROME_DESCRIPTIONS.get(alternative) and count:
                desc = settings.ROME_DESCRIPTIONS.get(alternative)
                slug = slugify(desc)
                alternative_rome_descriptions.append([alternative, desc, slug, count])
        company_count = fetcher.company_count
        alternative_distances = fetcher.alternative_distances


    # Pagination.
    from_number_param = int(kwargs.get('from') or 1)
    to_number_param = int(kwargs.get('to') or 10)
    pagination_manager = PaginationManager(company_count, from_number_param, to_number_param, request.full_path)
    current_page = pagination_manager.get_current_page()

    # Get contact mode and position.
    for position, company in enumerate(companies, start=1):
        company.contact_mode = util.get_contact_mode_for_rome_and_naf(fetcher.rome, company.naf)
        # position is later used in labonneboite/web/static/js/results.js
        company.position = position

    # If a NAF filter is selected, previous naf_aggregations returned by fetcher.get_companies()
    # was actually only one NAF, the one NAF currently selected in the filter.
    # Let's do a second call, only if a NAF filter is selected.
    # This logic is designed to make only one elasticsearch call in the most frequent case (no NAF filter selected)
    # and make two elasticsearch calls in the rarest case only (NAF filter selected).
    if kwargs.get("naf"):
        naf_aggregations = fetcher.get_naf_aggregations()

    naf_codes_with_descriptions = []
    for naf_aggregate in naf_aggregations:
        naf_description = '%s (%s)' % (settings.NAF_CODES.get(naf_aggregate["naf"]), naf_aggregate["count"])
        naf_codes_with_descriptions.append((naf_aggregate["naf"], naf_description))

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
        'distance': kwargs['distance'],
        'doorbell_tags': doorbell.get_tags('results'),
        'form': form,
        'headcount': kwargs['headcount'],
        'job_doesnt_exist': False,
        'location': full_location,
        'zipcode_is_invalid': zipcode_is_invalid,
        'naf': kwargs['naf'],
        'naf_codes': naf_codes_with_descriptions,
        'page': current_page,
        'pagination': pagination_manager,
        'rome_code': rome,
        'rome_description': settings.ROME_DESCRIPTIONS.get(fetcher.rome, ''),
        'show_favorites': True,
        'sort': kwargs['sort'],
        'tile_server_url': settings.TILE_SERVER_URL,
        'user_favs_as_sirets': UserFavoriteOffice.user_favs_as_sirets(current_user),
        'zipcode': zipcode,
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
