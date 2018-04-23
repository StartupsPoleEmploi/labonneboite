# coding: utf8

from flask import redirect, url_for
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

    PUBLIC_CHOICES = (
        (unicode(search.PUBLIC_ALL), u'Tout'),
        (unicode(search.PUBLIC_JUNIOR), u'<span class="badge badge-large badge-info" data-toggle="tooltip" title="moins de 26 ans">Junior</span>'),
        (unicode(search.PUBLIC_SENIOR), u'<span class="badge badge-large badge-info" data-toggle="tooltip" title="plus de 50 ans">Senior</span>'),
        (unicode(search.PUBLIC_HANDICAP), u'<span class="badge badge-large badge-info" data-toggle="tooltip" title="Bénéficiaire de l\'Obligation d\'Emploi">BOE</span>'),
    )

    class Meta:
        # CSRF validation is enabled globally but we don't want the CSRF token
        # to be included in this form.
        # The token can be removed safely here because this form is always submitted in GET.
        # See http://goo.gl/QxWXBH for CSRF token with the GET method: server-side actions
        # that have state changing affect should only respond to POST requests.
        csrf = False

    job = StringField(u'', validators=[DataRequired()])
    location = StringField(u'', validators=[DataRequired()])

    latitude = DecimalField(widget=HiddenInput(), validators=[DataRequired(), NumberRange(-90, 90)])
    longitude = DecimalField(widget=HiddenInput(), validators=[DataRequired(), NumberRange(-180, 180)])

    occupation = HiddenField(u'', validators=[DataRequired()])

    headcount = RadioField(
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

    distance = RadioField(
        u'Distance',
        choices=DISTANCE_CHOICES,
        default=settings.DISTANCE_FILTER_DEFAULT,
        validators=[Optional()])

    flag_alternance = RadioField(
        u'Type de contrat',
        choices=FLAG_ALTERNANCE_CHOICES,
        default=0,
        validators=[Optional()])

    public = RadioField(
        u'Public',
        choices=PUBLIC_CHOICES,
        default=0,
        validators=[Optional()])

    def redirect(self, endpoint):
        # TODO remove this method, which will be useless once we got rid of the search.recherche endpoint
        values = {
            # 'city': city_slug,
            # 'zipcode': zipcode,
            'lat': self.latitude.data,
            'lon': self.longitude.data,
            'occupation': self.occupation.data,
        }
        if self.location.data:
            values['l'] = self.location.data
        if self.naf.data:
            values['naf'] = self.naf.data
        if self.sort.data:
            values['sort'] = self.sort.data
        if self.distance.data:
            values['d'] = self.distance.data
        if self.headcount.data:
            values['h'] = self.headcount.data
        if self.flag_alternance.data:
            values['f_a'] = self.flag_alternance.data
        if pro.pro_version_enabled():
            if self.public.data:
                values['p'] = self.public.data
        return redirect(url_for(endpoint, **values))
