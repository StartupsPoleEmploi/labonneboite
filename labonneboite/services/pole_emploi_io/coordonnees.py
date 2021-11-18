from typing import Dict
from requests import get
from labonneboite.conf import settings

from ..get_full_adress import get_full_adress
from .base import PEIOGetterBase


class CoordonneesGetter(PEIOGetterBase):
    url = f"{settings.PEAM_API_BASE_URL}/partenaire/peconnect-coordonnees/v1/coordonnees"

    def fetch(self):
        retrieved_address = super().fetch()
        full_address = self._format_full_address(retrieved_address)

        return {
            **retrieved_address,
            "fullAddress": full_address,
        }

    def _format_full_address(self, retrieved_address: Dict):
        return get_full_adress(
            None,
            retrieved_address.get("adresse1"),
            retrieved_address.get("codePostal"),
            retrieved_address.get("libelleCommune", "").title() or None,
        )

    def _fetch_candidate_address(self):
        return {
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
