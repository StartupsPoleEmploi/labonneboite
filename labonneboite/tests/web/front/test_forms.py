from werkzeug.datastructures import MultiDict

from labonneboite.web.search.forms import CompanySearchForm
from labonneboite.tests.test_base import AppTest

"""
    Tests for the forms of labonneboite/web/search/forms.py
    Note that there is also labonneboite/tests/web/front/test_contact_form.py
"""

class SearchFormTest(AppTest):
    def test_validate_missing_longlat_departments(self):
        with self.app_context():
            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
                'departments': '1, 2, 3',
            }))
            self.assertEqual(form.validate(), True)

            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
                'lon': '1',
                'lat': '2',
            }))
            self.assertEqual(form.validate(), True)

            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
                'lon': '1',
            }))
            self.assertEqual(form.validate(), False)

            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
                'lat': '2',
            }))
            self.assertEqual(form.validate(), False)

            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
            }))
            self.assertEqual(form.validate(), False)

    def test_validate_departments(self):
        with self.app_context():
            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
                'departments': '1,2'
            }))
            self.assertEqual(form.validate(), True)

            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
                'departments': '1, 2, 3'
            }))
            self.assertEqual(form.validate(), True)

            form = CompanySearchForm(MultiDict({
                'j': 'test j',
                'l': 'test l',
                'occupation': 'test occupation',
                'departments': 'a,b'
            }))
            self.assertEqual(form.validate(), False)
