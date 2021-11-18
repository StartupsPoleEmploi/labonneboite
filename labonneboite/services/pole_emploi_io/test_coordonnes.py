from unittest import TestCase, mock
from .coordonnees import CoordonneesGetter, PEIOGetterBase

class TestCoordonnees(TestCase):

    @mock.patch.object(
        PEIOGetterBase, 'fetch', return_value={
            "adresse1": "Complément Destinataire",
            "adresse2": "Complément Adresse",
            "adresse3": "Complément Distribution",
            "adresse4": "Voie",
            "codePostal": "44000",
            "codeINSEE": "44109",
            "libelleCommune": "NANTES",
            "codePays": "FR",
            "libellePays": "FRANCE"
        }
    )
    def testGetter(self, baseFetch: mock.MagicMock):
        self.assertDictEqual(CoordonneesGetter('access_token').fetch(), {
            "adresse1": "Complément Destinataire",
            "adresse2": "Complément Adresse",
            "adresse3": "Complément Distribution",
            "adresse4": "Voie",
            "codePostal": "44000",
            "codeINSEE": "44109",
            "libelleCommune": "NANTES",
            "codePays": "FR",
            "libellePays": "FRANCE",
            "fullAddress": "Complément Destinataire 44000 Nantes",
        })
