from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from wtforms import validators
from wtforms.validators import DataRequired

from labonneboite.common import scoring
from labonneboite.common.models import OfficeAdminRemove, OfficeAdminAdd
from labonneboite.common.scoring import get_hirings_from_score
from labonneboite.conf import settings
from labonneboite.web.admin.forms import code_commune_validator, zip_code_validator
from labonneboite.web.admin.forms import (
    nospace_filter,
    phone_validator,
    strip_filter,
    siret_validator,
    naf_validator,
)
from labonneboite.web.admin.utils import (
    datetime_format,
    AdminModelViewMixin,
    SelectForChoiceTypeField,
)
from labonneboite.scripts import create_index


class OfficeAdminAddModelView(AdminModelViewMixin, ModelView):  # type: ignore
    """
    Admin interface for the `OfficeAdminAdd` model.
    http://flask-admin.readthedocs.io/en/latest/api/mod_model/
    """

    can_delete = False
    can_edit = False
    can_view_details = True
    column_searchable_list = ["siret", "company_name", "office_name"]
    column_default_sort = ("date_created", True)
    page_size = 100

    column_list = [
        "siret",
        "company_name",
        "reason",
        "date_created",
        "date_updated",
    ]

    column_details_list = [
        "siret",
        "company_name",
        "office_name",
        "naf",
        "street_number",
        "street_name",
        "zipcode",
        "city_code",
        "email",
        "tel",
        "website",
        "flag_alternance",
        "flag_junior",
        "flag_senior",
        "flag_handicap",
        "departement",
        "headcount",
        "hiring",
        "score_alternance",
        "x",
        "y",
        "reason",
        "created_by",
        "date_created",
        "updated_by",
        "date_updated",
    ]

    column_formatters = {
        "date_created": datetime_format,
        "date_updated": datetime_format,
    }

    column_labels = {
        "siret": "Siret",
        "company_name": "Raison sociale",
        "office_name": "Enseigne",
        "naf": "Code NAF",
        "street_number": "Numero rue",
        "street_name": "Libellé rue",
        "zipcode": "Code postal",
        "city_code": "Code commune",
        "email": "Email",
        "tel": "Téléphone",
        "website": "Site web",
        "flag_alternance": "Drapeau alternance",
        "flag_junior": "Drapeau junior",
        "flag_senior": "Drapeau senior",
        "flag_handicap": "Drapeau handicap",
        "departement": "Département",
        "headcount": "Tranche effectif",
        "hiring": "hiring",
        "score_alternance": "Score alternance",
        "x": "Longitude",
        "y": "Latitude",
        "reason": "Raison",
        "date_created": "Date de création",
        "date_updated": "Date de modification",
        "created_by": "Créé par",
        "updated_by": "Modifié par",
    }

    column_descriptions = {
        "reason": "Raison de l'ajout.",
        "hiring": "Valeur recommandée : entre "
        f"{scoring.get_hirings_from_score(80)} et {scoring.get_hirings_from_score(90)}",
        "score_alternance": "Valeur recommandée : entre 80 et 90",
    }

    form_columns = [
        "siret",
        "company_name",
        "office_name",
        "naf",
        "street_number",
        "street_name",
        "zipcode",
        "city_code",
        "departement",
        "email",
        "tel",
        "website",
        "flag_alternance",
        "flag_junior",
        "flag_senior",
        "flag_handicap",
        "headcount",
        "hiring",
        "score_alternance",
        "y",
        "x",
        "reason",
    ]

    form_overrides = {
        "headcount": SelectForChoiceTypeField,
    }

    form_args = {
        "siret": {
            "filters": [strip_filter, nospace_filter],
            "validators": [DataRequired(), siret_validator],
        },
        "company_name": {
            "filters": [strip_filter],
        },
        "office_name": {
            "filters": [strip_filter],
        },
        "naf": {
            "filters": [strip_filter, nospace_filter],
            "validators": [naf_validator],
        },
        "street_number": {
            "filters": [strip_filter, nospace_filter],
        },
        "street_name": {
            "filters": [strip_filter],
        },
        "zipcode": {
            "filters": [strip_filter, nospace_filter],
            "validators": [zip_code_validator],
        },
        "city_code": {
            "filters": [strip_filter, nospace_filter],
            "validators": [code_commune_validator],
        },
        "departement": {
            "filters": [strip_filter, nospace_filter],
        },
        "email": {
            "validators": [validators.optional(), validators.Email()],
        },
        "tel": {
            "filters": [strip_filter, nospace_filter],
            "validators": [validators.optional(), phone_validator],
        },
        "website": {
            "filters": [strip_filter],
            "validators": [validators.optional(), validators.URL()],
        },
        "headcount": {
            "choices": settings.HEADCOUNT_INSEE_CHOICES,
        },
        "hiring": {
            "validators": [
                validators.NumberRange(min=0, max=get_hirings_from_score(100))
            ],
        },
        "score_alternance": {
            "validators": [validators.NumberRange(min=0, max=100)],
        },
        "reason": {
            "filters": [strip_filter],
        },
        "x": {
            "filters": [strip_filter, nospace_filter],
            "validators": [DataRequired()],
        },
        "y": {
            "filters": [strip_filter, nospace_filter],
            "validators": [DataRequired()],
        },
    }

    def after_model_change(
        self, form: BaseForm, model: OfficeAdminAdd, is_created: bool
    ) -> None:
        """
        Add new office in ElacticSearch and MySQL DB and remove it from OfficeAdminRemove
        if it exists in such DB
        """
        OfficeAdminRemove.query.filter_by(siret=form.data["siret"]).delete()
        create_index.add_individual_office(model)
