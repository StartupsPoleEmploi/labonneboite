# coding: utf8

from flask import url_for
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common.models import Office, OfficeAdminAdd, OfficeAdminRemove, OfficeAdminUpdate
from labonneboite.tests.scripts.test_create_index import CreateIndexBaseTest
from labonneboite.web.office.views import make_save_suggestion


class SaveSuggestionsTest(CreateIndexBaseTest):
    def test_no_company_found(self):
        # No company and no OfficeAdminRemove
        form = {
            'siret': u'Invalid'
        }
        self.assertEquals(u'Aucune entreprise trouvée avec le siret Invalid', make_save_suggestion(form))
