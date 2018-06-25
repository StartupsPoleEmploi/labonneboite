# coding: utf8

from flask_wtf import FlaskForm
from wtforms import HiddenField, ValidationError


class UserAccountDeleteForm(FlaskForm):
    """
    Confirm the deletion of a user account.
    The main interest of this form is that it put the CSRF token automatically in a hidden field.
    """

    confirm_deletion = HiddenField(default=1)

    def validate_confirm_deletion(self, field):
        """
        That shouldn't happen at all but it serves as an additional layer of safety.
        """
        if field.data != "1":
            raise ValidationError()
