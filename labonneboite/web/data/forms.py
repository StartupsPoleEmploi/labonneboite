# coding: utf8

from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError
from wtforms.validators import DataRequired

from labonneboite.common.models import Office
from labonneboite.conf import settings
from labonneboite.conf.common.naf_codes import NAF_CODES
from labonneboite.web.admin.forms import siret_validator


class NafForm(FlaskForm):
    """
    Enter a NAF code to find associated ROME codes.
    """
    naf = StringField(u"NAF", validators=[DataRequired()],
        description=u"Saisissez un code NAF pour trouver les codes ROME associés.")

    class Meta:
        # CSRF validation is enabled globally but we don't want the CSRF token
        # to be included in this form.
        # The token can be removed safely here because this form is always submitted in GET.
        # See http://goo.gl/QxWXBH for CSRF token with the GET method: server-side actions
        # that have state changing affect should only respond to POST requests.
        csrf = False

    def validate_naf(self, field):
        if field.data and field.data not in NAF_CODES:
            raise ValidationError(u"Ce code NAF n'est pas valide.")


class RomeForm(FlaskForm):
    """
    Enter a ROME code to find associated NAF codes.
    """
    rome = StringField(u"ROME", validators=[DataRequired()],
        description=u"Saisissez un code ROME pour trouver les codes NAF associés.")

    class Meta:
        # CSRF validation is enabled globally but we don't want the CSRF token
        # to be included in this form.
        # The token can be removed safely here because this form is always submitted in GET.
        # See http://goo.gl/QxWXBH for CSRF token with the GET method: server-side actions
        # that have state changing affect should only respond to POST requests.
        csrf = False

    def validate_rome(self, field):
        if field.data and field.data not in settings.ROME_DESCRIPTIONS:
            raise ValidationError(u"Ce code ROME n'est pas valide.")


class SiretForm(FlaskForm):
    """
    Enter a SIRET to find associated ROME codes.
    """
    siret = StringField(u"Siret", validators=[DataRequired(), siret_validator],
        description=u"Saisissez un SIRET pour trouver les codes ROME associés.")

    class Meta:
        # CSRF validation is enabled globally but we don't want the CSRF token
        # to be included in this form.
        # The token can be removed safely here because this form is always submitted in GET.
        # See http://goo.gl/QxWXBH for CSRF token with the GET method: server-side actions
        # that have state changing affect should only respond to POST requests.
        csrf = False

    def validate_siret(self, field):
        # Do not perform the query if the form already has errors.
        if not self.errors and field.data:
            office = Office.query.filter_by(siret=self.data['siret']).first()
            if not office:
                raise ValidationError(u"Ce SIRET n'existe pas.")
            # Set office as a form attribute for easy access in the view and to avoid another query.
            self.office = office
