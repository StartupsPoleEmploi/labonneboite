# coding: utf8

from flask import redirect, url_for
from flask_wtf import FlaskForm
from slugify import slugify
from wtforms import StringField, SelectField, HiddenField, RadioField
from wtforms.validators import DataRequired, Optional

from labonneboite.conf import settings
from labonneboite.common import util
from labonneboite.common import search


class CompanySearchForm(FlaskForm):

    HEADCOUNT_CHOICES = (
        (u'1', u'Toutes tailles'),
        (u'2', u'Moins de 50 salariés'),
        (u'3', u'Plus de 50 salariés'),
    )

    SORTING_CHOICES = (
        (u'distance', u'Distance'),
        (u'score', u'Potentiel d\'embauche'),
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
        (u'1', u'Alternance'),
    )

    PUBLIC_CHOICES = (
        (str(search.PUBLIC_ALL).decode('utf-8'), u'Tout'),
        (str(search.PUBLIC_JUNIOR).decode('utf-8'), u'Junior uniquement <small class="badge badge-info" data-toggle="tooltip" title="moins de 26 ans">?</small>'),
        (str(search.PUBLIC_SENIOR).decode('utf-8'), u'Senior uniquement <small class="badge badge-info" data-toggle="tooltip" title="plus de 50 ans">?</small>'),
        (str(search.PUBLIC_HANDICAP).decode('utf-8'), u'BOE uniquement <small class="badge badge-info" data-toggle="tooltip" title="Bénéficiaire de l\'Obligation d\'Emploi">?</small>'),
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

    city = HiddenField(u'', validators=[DataRequired()])
    zipcode = HiddenField(u'', validators=[DataRequired()])
    occupation = HiddenField(u'', validators=[DataRequired()])

    headcount = RadioField(
        u'Taille d\'entreprise',
        default=1,
        choices=HEADCOUNT_CHOICES,
        validators=[Optional()])

    sort = RadioField(
        u'Classement par',
        choices=SORTING_CHOICES,
        default=settings.SORT_FILTER_DEFAULT,
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
        city = self.city.data
        zipcode = self.zipcode.data
        occupation = self.occupation.data
        values = {
            'city': slugify(city),
            'zipcode': zipcode,
            'occupation': occupation,
        }
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
        if util.user_is_pro():
            if self.public.data:
                values['p'] = self.public.data
        return redirect(url_for(endpoint, **values))
