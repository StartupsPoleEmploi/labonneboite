# coding: utf8
"""
This blueprint provides ways to easily explore the internal ROME/NAF mapping.
"""
from flask import Blueprint
from flask import redirect, render_template, request, url_for

from labonneboite.common import mapping as mapping_util
from labonneboite.conf import settings
from labonneboite.conf.common.naf_codes import NAF_CODES
from labonneboite.web.data.forms import NafForm, RomeForm, SiretForm


dataBlueprint = Blueprint('data', __name__)


@dataBlueprint.route('/', methods=['GET'])
def home():
    """
    A convenience route, so the user can just enter the URL `/data` to easily access underlying views.
    """
    return redirect(url_for('data.romes_for_naf'))


@dataBlueprint.route('/romes-for-naf', methods=['GET'])
def romes_for_naf():
    """
    Find ROME codes associated with a given NAF code.
    """
    naf = request.args.get('naf')
    naf_name = None
    romes = None
    form = NafForm(naf=naf)

    if naf and form.validate():
        naf = form.naf.data
        naf_name = NAF_CODES.get(naf)
        mapper = mapping_util.Rome2NafMapper()
        romes = mapper.romes_for_naf(naf)

    context = {
        'current_tab': 'romes_for_naf',
        'form': form,
        'naf': naf,
        'naf_name': naf_name,
        'romes': romes,
    }
    return render_template('data/romes_for_naf.html', **context)


@dataBlueprint.route('/nafs-for-rome', methods=['GET'])
def nafs_for_rome():
    """
    Find NAF codes associated with a given ROME code.
    """
    rome = request.args.get('rome')
    rome_name = None
    nafs = None
    form = RomeForm(rome=rome)

    if rome and form.validate():
        rome = form.rome.data
        rome_name = settings.ROME_DESCRIPTIONS.get(rome)
        mapper = mapping_util.Rome2NafMapper()
        nafs = mapper.nafs_for_rome(rome)

    context = {
        'current_tab': 'nafs_for_rome',
        'form': form,
        'nafs': nafs,
        'rome': rome,
        'rome_name': rome_name,
    }
    return render_template('data/nafs_for_rome.html', **context)


@dataBlueprint.route('/romes-for-siret', methods=['GET'])
def romes_for_siret():
    """
    Find ROME codes associated with a given SIRET.
    """
    siret = request.args.get('siret')
    naf = None
    naf_name = None
    romes = None
    form = SiretForm(siret=siret)

    if siret and form.validate():
        naf = form.office.naf
        naf_name = NAF_CODES.get(naf)
        siret = form.siret.data
        mapper = mapping_util.Rome2NafMapper()
        romes = mapper.romes_for_naf(naf)

    context = {
        'current_tab': 'romes_for_siret',
        'form': form,
        'naf': naf,
        'naf_name': naf_name,
        'romes': romes,
        'siret': siret,
    }
    return render_template('data/romes_for_siret.html', **context)
