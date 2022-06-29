from collections import defaultdict
from typing import Sequence

from labonneboite.common import esd, geocoding, hiring_type_util
from labonneboite.common.chunks import chunks
from labonneboite.common.fetcher import Fetcher
from labonneboite.common.models import Office, OfficeResult
from labonneboite.common.conf import settings

OFFRES_ESD_ENDPOINT_URL = "%s/partenaire/offresdemploi/v2/offres/search" % settings.PEAM_API_BASE_URL
OFFRES_ESD_MAXIMUM_ROMES = 3
OFFRES_ESD_MAXIMUM_PAGE_SIZE = 150
OFFRES_ESD_MAXIMUM_DISTANCE = 200

# FIXME: if only contract = alternance is supported, remove the param hiring_type
#        and this contract feature here
HIRING_TYPE_TO_CONTRACT_NATURE_CODES = {
    hiring_type_util.ALTERNANCE: ["E2", "FS"],
}


class VisibleMarketFetcher(Fetcher):
    """
    Fetch offices having at least one job offer from the ESD Offers API.
    Internally fetches offers first then group them by their parent office.
    """

    def __init__(
            self,
            romes,
            commune_id,
            distance,
            hiring_type,
            page_size,
    ):
        self.romes = romes
        self.commune_id = commune_id
        self.distance = distance
        self.hiring_type = hiring_type
        self.page_size = page_size

    def get_contract_nature_codes(self):
        return HIRING_TYPE_TO_CONTRACT_NATURE_CODES[self.hiring_type]

    def get_offices(self) -> Sequence[OfficeResult]:
        offers = self.get_offers_for_romes(self.romes)

        office_key_to_offers = defaultdict(list)
        for offer in offers:
            offer_is_valid = (
                    'entreprise' in offer
                    and 'siret' in offer['entreprise']
                    and 'lieuTravail' in offer
                    and 'latitude' in offer['lieuTravail']
                    and 'longitude' in offer['lieuTravail']
            )
            if offer_is_valid:
                office_key = offer['entreprise']['siret']
                office_key_to_offers[office_key].append(offer)

        # Fetch matching offices from db. Offers without a match
        # will silently be dropped.
        offices = Office.query.filter(Office.siret.in_(office_key_to_offers.keys()), ).limit(self.page_size).all()
        self.office_count = len(offices)

        office_results: List[OfficeResult] = []
        # Add extra fields to each office to enrich the API JSON response.
        # - `distance` : distance between the office and the search location, same as
        #                in a regular hidden market search.
        # - `offer_count` and `offers` : useful minimalistic information about the offers found
        #                for this office.
        # - `matched_rome` : rome which matched on the query
        for office in offices:
            office_offers = office_key_to_offers[office.siret]
            first_offer = office_offers[0]
            office_result = OfficeResult(office)
            office_distance = geocoding.get_distance_between_commune_id_and_coordinates(
                commune_id=self.commune_id,
                latitude=first_offer['lieuTravail']['latitude'],
                longitude=first_offer['lieuTravail']['longitude'],
            )
            office_result.distance = round(office_distance, 1)

            office_result.matched_rome = first_offer['romeCode']
            office_result.offers_count = len(office_offers)
            office_result.offers = [{
                'id': offer['id'],
                'name': offer['intitule'],
                'url': offer['origineOffre']['urlOrigine'],
            } for offer in office_offers]
            # Contact data coming from offers take precedence
            # over LBB ones.
            for offer in office_offers:
                if 'contact' in offer:
                    # FIXME: the address API will soon remove the emails
                    if 'courriel' in offer:  # FIXME: this should be if 'courriel' in offer['contact']
                        office_result.email = offer['contact']['courriel']
                    if 'telephone' in offer:  # FIXME: same error to fix here
                        office_result.tel = offer['contact']['telephone']
                    if 'urlPostulation' in offer:  # FIXME: same error to fix here
                        office_result.website = offer['contact']['urlPostulation']
                    elif 'urlRecruteur' in offer:  # FIXME: same error to fix here
                        office_result.website = offer['contact']['urlRecruteur']
            office_results.append(office_result)

        return office_results

    def get_offers_for_romes(self, romes):
        offers = []

        for romes_batch in chunks(romes, OFFRES_ESD_MAXIMUM_ROMES):
            url = OFFRES_ESD_ENDPOINT_URL
            params = {
                'range': "0-{}".format(OFFRES_ESD_MAXIMUM_PAGE_SIZE - 1),
                'sort': 1,
                'codeROME': ",".join(romes_batch),
                'natureContrat': ",".join(self.get_contract_nature_codes()),
                'commune': self.commune_id,
                'distance': min(self.distance, OFFRES_ESD_MAXIMUM_DISTANCE),
            }
            response = esd.get_response(url, params)
            # Convenient reminder to dump json to file for test mockups.
            # json.dump(response, json_file, sort_keys=True, indent=4)
            offers += response['resultats']

        return offers
