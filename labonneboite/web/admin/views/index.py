"""
The admin interface is built on top of Flask-Admin:
- https://flask-admin.readthedocs.io/en/latest/
- http://flask-admin.readthedocs.io/en/latest/api/mod_model/
- http://mrjoes.github.io/2015/06/17/flask-admin-120.html
"""
from flask_admin import AdminIndexView, expose

from labonneboite.web.admin.utils import abort_if_not_admin, user_is_admin


class LbbAdminIndexView(AdminIndexView):
    """
    A custom index view class for the LBB admin.
    """

    @expose("/")
    def index(self):
        if user_is_admin():
            return super(LbbAdminIndexView, self).index()
        return abort_if_not_admin()
