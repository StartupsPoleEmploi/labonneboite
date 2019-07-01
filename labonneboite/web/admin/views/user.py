from flask_admin.contrib.sqla import ModelView

from labonneboite.web.admin.utils import AdminModelViewMixin


class UserModelView(AdminModelViewMixin, ModelView):
    """
    Admin interface for the `User` model.
    """

    can_create = False
    can_delete = False
    can_view_details = True
    column_searchable_list = ['email', 'first_name', 'last_name']
    page_size = 100

    column_list = [
        'id',
        'email',
        'first_name',
        'last_name',
        'date_created',
        'active',
        'is_admin',
    ]

    column_labels = {
        'gender':  "Genre",
        'first_name': "Prénom",
        'last_name': "Nom",
        'date_created': "Date de création",
        'active': "Actif",
        'external_id': "ID externe",
        'is_admin': "Admin",
    }

    form_columns = ['active', 'is_admin']
