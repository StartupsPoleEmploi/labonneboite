# coding: utf8

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, RadioField, DecimalField
from wtforms.validators import DataRequired, Optional, NumberRange
from wtforms.widgets import HiddenInput

from labonneboite.conf import settings
from labonneboite.common import pro
from labonneboite.common import search
from labonneboite.common import sorting


class CompanySearchForm(FlaskForm):
    """
    This form is used only for rendering, not for validation.
    """

    HEADCOUNT_CHOICES = (
        (u'1', u'Toutes tailles'),
        (u'2', u'Moins de 50 salariés'),
        (u'3', u'Plus de 50 salariés'),
    )

    NAF_CHOICES = [('', u'Tous les secteurs')] + [(k, v) for k, v in settings.NAF_CODES.items()]

    DISTANCE_XS = u'10'
    DISTANCE_S = u'30'
    DISTANCE_M = u'50'
    DISTANCE_L = u'100'
    DISTANCE_XL = u'3000'

    DISTANCE_CHOICES = (
        (DISTANCE_XS, u'Moins de 10 km'),
        (DISTANCE_S, u'Moins de 30 km'),
        (DISTANCE_M, u'Moins de 50 km'),
        (DISTANCE_L, u'Moins de 100km'),
        (DISTANCE_XL, u'France entière')
    )

    FLAG_ALTERNANCE_CHOICES = (
        (u'0', u'Tous types'),
        (u'1', u'<span class="badge badge-large badge-alternance">Alternance</span>'),
    )

    class Meta:
        # CSRF validation is enabled globally but we don't want the CSRF token
        # to be included in this form.
        # The token can be removed safely here because this form is always submitted in GET.
        # See http://goo.gl/QxWXBH for CSRF token with the GET method: server-side actions
        # that have state changing affect should only respond to POST requests.
        csrf = False

    # Typed job
    j = StringField(u'Job', validators=[DataRequired()])
    # Corresponding occupation found by autocomplete
    occupation = HiddenField(u'', validators=[DataRequired()])

    # Typed location
    l = StringField(u'Location', validators=[DataRequired()])
    # Corresponding coordinates found by autocomplete
    lat = DecimalField(widget=HiddenInput(), validators=[DataRequired(), NumberRange(-90, 90)])
    lon = DecimalField(widget=HiddenInput(), validators=[DataRequired(), NumberRange(-180, 180)])

    # Headcount
    h = RadioField(
        u'Taille d\'entreprise',
        default=1,
        choices=HEADCOUNT_CHOICES,
        validators=[Optional()])

    sort = RadioField(
        u'Classement par',
        choices=sorting.SORTING_CHOICES,
        default=sorting.SORT_FILTER_DEFAULT,
        validators=[Optional()])

    naf = SelectField(
        u'Secteur d\'activité',
        choices=NAF_CHOICES,
        default='',
        validators=[Optional()])

    # TODO form will not validate for distance=5... (this concerns many requests/day)
    d = RadioField(
        u'Distance',
        choices=DISTANCE_CHOICES,
        default=settings.DISTANCE_FILTER_DEFAULT,
        validators=[Optional()])

    f_a = RadioField(
        u'Type de contrat',
        choices=FLAG_ALTERNANCE_CHOICES,
        default=0,
        validators=[Optional()])


class ProCompanySearchForm(CompanySearchForm):

    PUBLIC_CHOICES = (
        (unicode(search.PUBLIC_ALL), u'Tout'),
        (unicode(search.PUBLIC_JUNIOR), u'<span class="badge badge-large badge-info" data-toggle="tooltip" title="moins de 26 ans">Junior</span>'),
        (unicode(search.PUBLIC_SENIOR), u'<span class="badge badge-large badge-info" data-toggle="tooltip" title="plus de 50 ans">Senior</span>'),
        (unicode(search.PUBLIC_HANDICAP), u'<span class="badge badge-large badge-info" data-toggle="tooltip" title="Bénéficiaire de l\'Obligation d\'Emploi">BOE</span>'),
    )

    # this field is activated only in pro mode
    p = RadioField(
        u'Public',
        choices=PUBLIC_CHOICES,
        default=0,
        validators=[Optional()])


def make_company_search_form(**kwargs):
    if pro.pro_version_enabled():
        return ProCompanySearchForm(**kwargs)
    return CompanySearchForm(**kwargs)
