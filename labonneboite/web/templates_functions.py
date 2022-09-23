import jinja2
from flask import Flask


class MobivilleCompany:

    name="LA ROCHELLE, STRASBOURG, LIMOGES ...."
    naf_text='Trouvez l’emploi et la ville qui va avec !'

    def get_stars_for_rome_code_as_percentage(self, _=None):
        return 100

    def get_stars_for_rome_code(self, _=None):
        return 5


def include_file(flask_app: Flask):
    def include_file(filename):
        return jinja2.utils.markupsafe.Markup.escape(flask_app.jinja_loader.get_source(flask_app.jinja_env, filename)[0])
    return include_file


def register_templates_functions(flask_app: Flask):
    flask_app.add_template_global(MobivilleCompany, name='mobiville_company')
    flask_app.add_template_global(include_file(flask_app), name='include_file')