# coding: utf8

from flask import Blueprint, current_app
from flask import abort, send_from_directory, redirect, render_template, request

from labonneboite.common import doorbell
from labonneboite.common import pro
from labonneboite.conf import settings
from labonneboite.web.search.forms import CompanySearchForm
from labonneboite.web.utils import fix_csrf_session


rootBlueprint = Blueprint('root', __name__)


@rootBlueprint.route('/')
def home():
    fix_csrf_session()
    return render_template('home.html', form=CompanySearchForm())

@rootBlueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(current_app.static_folder, 'images/favicon.ico')

@rootBlueprint.route('/robots.txt')
@rootBlueprint.route('/googleaece67026df0ee76.html')
def static_from_root():
    return send_from_directory(current_app.static_folder, request.path[1:])


@rootBlueprint.route('/kit.pdf')
def kit():
    if pro.pro_version_enabled():
        return send_from_directory(current_app.static_folder, 'kit.pdf')
    abort(404)


@rootBlueprint.route('/espace-presse')
def press():
    context = {
        'doorbell_tags': doorbell.get_tags('press'),
    }
    return render_template('root/press.html', **context)

@rootBlueprint.route('/accessibilite')
def accessibility():
    return render_template('root/accessibility.html')


@rootBlueprint.route('/comment-faire-une-candidature-spontanee')
def lbb_help():
    context = {
        'doorbell_tags': doorbell.get_tags('help'),
    }
    return render_template('root/help.html', **context)


@rootBlueprint.route('/faq')
def faq():
    context = {
        'doorbell_tags': doorbell.get_tags('faq'),
    }
    return render_template('root/faq.html', **context)


@rootBlueprint.route('/conditions-generales')
def cgu():
    host = settings.SERVER_NAME
    return render_template('root/cgu.html', host=host)


@rootBlueprint.route('/cookbook')
def cookbook():
    return render_template('root/cookbook.html')


@rootBlueprint.route('/stats')
def stats():
    return redirect('https://datastudio.google.com/open/0B0PPPCjOppNIdVNXVVM0QnJHNEE')
