import datetime

from flask import abort
from flask_login import current_user
from sqlalchemy_utils import Choice
from wtforms import SelectField


def user_is_admin():
    """
    Returns True if the user can access the admin site.
    """
    return current_user.is_authenticated and current_user.active and current_user.is_admin


def abort_if_not_admin():
    """
    What happens if a non authorized user try to access an admin page.
    """
    return abort(404)


class AdminModelViewMixin(object):
    """
    A mixin that **must** be used in any model views that create a dedicated set of admin pages.
    """

    def is_accessible(self):
        return user_is_admin()

    def inaccessible_callback(self, name, **kwargs):
        return abort_if_not_admin()

    def on_model_change(self, form, model, is_created):
        if is_created:
            if hasattr(model, 'created_by'):
                model.created_by = current_user
        else:
            if hasattr(model, 'updated_by'):
                model.updated_by = current_user
            if hasattr(model, 'date_updated'):
                model.date_updated = datetime.datetime.utcnow()


def datetime_format(view, context, model, name):
    """
    A view column formatter that display a custom version of the full datetime in admin lists.
    """
    dt = getattr(model, name)
    if dt:
        return dt.strftime('%d/%m/%Y %H:%M')
    return ''


class SelectForChoiceTypeField(SelectField):
    """
    A select field which play nicely with `sqlalchemy_utils.ChoiceType` and Flask Admin.
    See:
    - https://github.com/flask-admin/flask-admin/issues/1134
    - https://stackoverflow.com/a/31081753
    - https://goo.gl/Gp62ZP
    """

    def process_data(self, value):
        if value is None:
            self.data = None
        else:
            try:
                if isinstance(value, Choice):
                    self.data = self.coerce(value.code)
                else:
                    self.data = self.coerce(value)
            except (ValueError, TypeError):
                self.data = None
