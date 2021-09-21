
from werkzeug.datastructures import MultiDict
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, RadioField, DecimalField
from wtforms.validators import DataRequired, Optional, NumberRange, Regexp
from wtforms.widgets import HiddenInput

from labonneboite.conf import settings
from labonneboite.common import pro
from labonneboite.common import sorting
from labonneboite.common.maps import constants as maps_constants
from labonneboite.common.search import AudienceFilter


class CompanySearchForm(FlaskForm):
    """
    This form is used only for rendering, not for validation.
    """

    HEADCOUNT_CHOICES = (
        ('1', 'Toutes tailles'),
        ('2', 'Moins de 50 salariés'),
        ('3', 'Plus de 50 salariés'),
    )

    NAF_CHOICES = [('', 'Tous les secteurs')] + [(k, v) for k, v in list(settings.NAF_CODES.items())]

    DISTANCE_CHOICES = (
        ('5', '5 km'),
        ('10', '10 km'),
        ('30', '30 km'),
        ('50', '50 km'),
        ('100', '100 km'),
        ('3000', '+ de 100 km'),
    )

    DURATION_CHOICES = [
        (str(dur), 'Moins de {:d} min'.format(dur)) for dur in maps_constants.ISOCHRONE_DURATIONS_MINUTES
    ]

    class Meta:
        # CSRF validation is enabled globally but we don't want the CSRF token
        # to be included in this form.
        # The token can be removed safely here because this form is always submitted in GET.
        # See http://goo.gl/QxWXBH for CSRF token with the GET method: server-side actions
        # that have state changing affect should only respond to POST requests.
        csrf = False

    # Typed job
    j = StringField('Métier recherché', validators=[DataRequired()])
    ij = HiddenField(validators=[Optional()])

    # Corresponding occupation found by autocomplete
    occupation = HiddenField('', validators=[DataRequired()])

    # Typed location
    l = StringField('Lieu de recherche', validators=[DataRequired()])
    # Corresponding coordinates found by autocomplete
    lat = DecimalField(widget=HiddenInput(), validators=[Optional(), NumberRange(-90, 90)])
    lon = DecimalField(widget=HiddenInput(), validators=[Optional(), NumberRange(-180, 180)])
    departments = StringField(widget=HiddenInput(), validators=[Optional(), Regexp('([0-9]+,?)+')])

    # Headcount
    h = RadioField(
        'Taille de l\'entreprise',
        default=1,
        choices=HEADCOUNT_CHOICES,
        validators=[Optional()])

    sort = RadioField(
        'Classement par',
        choices=sorting.SORTING_CHOICES,
        default=sorting.SORT_FILTER_DEFAULT,
        validators=[Optional()])

    naf = SelectField(
        'Secteur d\'activité',
        choices=NAF_CHOICES,
        default='',
        validators=[Optional()])

    d = RadioField(
        'Rayon de recherche',
        choices=DISTANCE_CHOICES,
        default=settings.DISTANCE_FILTER_DEFAULT,
        validators=[Optional()])

    tr = HiddenField(
        'Mode de transport',
        default=maps_constants.DEFAULT_TRAVEL_MODE,
        validators=[Optional()]
    )

    dur = RadioField(
        'Temps de trajet',
        choices=DURATION_CHOICES,
        validators=[Optional()]
    )

    def validate(self):
        """
            Custom validators
        """
        if not super(CompanySearchForm, self).validate():
            return False
        if not self.departments.data and (not self.lon.data or not self.lat.data):
            return False
        return True


class ProCompanySearchForm(CompanySearchForm):

    AUDIENCE_CHOICES = (
        (str(AudienceFilter.ALL.value), 'Tout'),
        (str(AudienceFilter.JUNIOR.value), '<span class="badge badge-large badge-info" data-toggle="tooltip" title="moins de 26 ans">Junior</span>'),
        (str(AudienceFilter.SENIOR.value), '<span class="badge badge-large badge-info" data-toggle="tooltip" title="plus de 50 ans">Senior</span>'),
        (str(AudienceFilter.HANDICAP.value), '<span class="badge badge-large badge-info" data-toggle="tooltip" title="Bénéficiaire de l\'Obligation d\'Emploi">BOE</span>'),
    )

    # this field is activated only in pro mode
    p = RadioField(
        'Public',
        choices=AUDIENCE_CHOICES,
        default=0,
        validators=[Optional()])


def make_company_search_form(**kwargs):
    if pro.pro_version_enabled():
        return ProCompanySearchForm(MultiDict(kwargs))
    return CompanySearchForm(MultiDict(kwargs))
