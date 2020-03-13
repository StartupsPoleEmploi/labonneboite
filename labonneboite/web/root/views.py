import requests
from flask import Blueprint, abort, current_app, redirect, render_template, request, send_from_directory

from labonneboite.common import activity, doorbell, pro
from labonneboite.conf import settings
from labonneboite.web.search.forms import CompanySearchForm
from labonneboite.web.utils import fix_csrf_session


rootBlueprint = Blueprint("root", __name__)


@rootBlueprint.route("/")
def home():
    fix_csrf_session()
    activity.log(
        event_name="home",
        # GA tracking is used in PSE 2019-2020 experiment
        utm_medium=request.args.get("utm_medium", ""),
        utm_source=request.args.get("utm_source", ""),
        utm_campaign=request.args.get("utm_campaign", ""),
    )
    return render_template("home.html", form=CompanySearchForm())


@rootBlueprint.route("/favicon.ico")
def favicon():
    return send_from_directory(current_app.static_folder, "images/favicon.ico")


@rootBlueprint.route("/robots.txt")
@rootBlueprint.route("/googleaece67026df0ee76.html")
def static_from_root():
    return send_from_directory(current_app.static_folder, request.path[1:])


@rootBlueprint.route("/kit.pdf")
def kit():
    if pro.pro_version_enabled():
        return send_from_directory(current_app.static_folder, "kit.pdf")
    abort(404)


@rootBlueprint.route("/espace-presse")
def press():
    context = {"doorbell_tags": doorbell.get_tags("press")}
    return render_template("root/press.html", **context)


@rootBlueprint.route("/accessibilite")
def accessibility():
    return render_template("root/accessibility.html")


@rootBlueprint.route("/comment-faire-une-candidature-spontanee")
def lbb_help():
    context = {"doorbell_tags": doorbell.get_tags("help")}
    return render_template("root/help.html", **context)


@rootBlueprint.route("/faq")
def faq():
    context = {"doorbell_tags": doorbell.get_tags("faq")}
    return render_template("root/faq.html", **context)


@rootBlueprint.route("/conditions-generales")
def cgu():
    host = settings.SERVER_NAME
    return render_template("root/cgu.html", host=host)


@rootBlueprint.route("/cookbook")
def cookbook():
    return render_template("root/cookbook.html")


@rootBlueprint.route("/stats")
def stats():
    return redirect("https://datastudio.google.com/open/0B0PPPCjOppNIdVNXVVM0QnJHNEE")


@rootBlueprint.route("/widget-esd")
def widget():
    try:
        return render_template("root/widget-esd.html", access_token=get_widget_access_token())
    except Exception as e:
        print(e)
        abort(418)


@rootBlueprint.route("/widget-esd-staging")
def widget_staging():
    try:
        return render_template("root/widget-esd-staging.html", access_token=get_widget_access_token())
    except Exception as e:
        print(e)
        abort(418)


def get_widget_access_token():
    ACCESS_TOKEN_URL = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"

    data = {
        "grant_type": "client_credentials",
        "client_id": settings.PEAM_CLIENT_ID,
        "client_secret": settings.PEAM_CLIENT_SECRET,
        "scope": "application_{} api_labonnealternancev1".format(settings.PEAM_CLIENT_ID),
    }

    resp = requests.post(
        ACCESS_TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, verify=False
    )
    response = resp.json()
    return response["access_token"]


@rootBlueprint.route("/widget-no-esd")
def widget_no_esd():
    return render_template("root/widget-no-esd.html")


@rootBlueprint.route("/widget-no-esd-staging")
def widget_no_esd_staging():
    return render_template("root/widget-no-esd-staging.html")
