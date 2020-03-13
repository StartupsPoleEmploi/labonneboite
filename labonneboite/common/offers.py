from collections import defaultdict

from labonneboite.common import esd, geocoding, hiring_type_util
from labonneboite.common.chunks import chunks
from labonneboite.common.fetcher import Fetcher
from labonneboite.common.models import Office
from labonneboite.conf import settings


OFFRES_ESD_ENDPOINT_URL = "%s/partenaire/offresdemploi/v2/offres/search" % settings.PEAM_API_BASE_URL
OFFRES_ESD_MAXIMUM_ROMES = 3
OFFRES_ESD_MAXIMUM_PAGE_SIZE = 150
OFFRES_ESD_MAXIMUM_DISTANCE = 200

HIRING_TYPE_TO_CONTRACT_NATURE_CODES = {hiring_type_util.ALTERNANCE: ["E2", "FS"]}


class VisibleMarketFetcher(Fetcher):
    """
    Fetch offices having at least one job offer from the ESD Offers API.
    Internally fetches offers first then group them by their parent office.
    """

    def __init__(self, romes, commune_id, distance, hiring_type, page_size):
        self.romes = romes
        self.commune_id = commune_id
        self.distance = distance
        self.hiring_type = hiring_type
        self.page_size = page_size

    def get_contract_nature_codes(self):
        return HIRING_TYPE_TO_CONTRACT_NATURE_CODES[self.hiring_type]

    def get_offices(self):
        offers = self.get_offers_for_romes(self.romes)

        office_key_to_offers = defaultdict(list)
        for offer in offers:
            offer_is_valid = (
                "entreprise" in offer
                and "siret" in offer["entreprise"]
                and "lieuTravail" in offer
                and "latitude" in offer["lieuTravail"]
                and "longitude" in offer["lieuTravail"]
            )
            if offer_is_valid:
                office_key = offer["entreprise"]["siret"]
                office_key_to_offers[office_key].append(offer)

        # Fetch matching offices from db. Offers without a match
        # will silently be dropped.
        offices = Office.query.filter(Office.siret.in_(office_key_to_offers.keys())).limit(self.page_size).all()

        # Add extra fields to each office to enrich the API JSON response.
        # - `distance` : distance between the office and the search location, same as
        #                in a regular hidden market search.
        # - `offer_count` and `offers` : useful minimalistic information about the offers found
        #                for this office.
        # - `matched_rome` : rome which matched on the query
        for office in offices:
            office_offers = office_key_to_offers[office.siret]
            first_offer = office_offers[0]

            office_distance = geocoding.get_distance_between_commune_id_and_coordinates(
                commune_id=self.commune_id,
                latitude=first_offer["lieuTravail"]["latitude"],
                longitude=first_offer["lieuTravail"]["longitude"],
            )
            office.distance = round(office_distance, 1)

            office.matched_rome = first_offer["romeCode"]
            office.offers_count = len(office_offers)
            office.offers = [
                {"id": offer["id"], "name": offer["intitule"], "url": offer["origineOffre"]["urlOrigine"]}
                for offer in office_offers
            ]
            # Contact data coming from offers take precedence
            # over LBB ones.
            for offer in office_offers:
                if "contact" in offer:
                    if "courriel" in offer:
                        office.email = offer["contact"]["courriel"]
                    if "telephone" in offer:
                        office.tel = offer["contact"]["telephone"]
                    if "urlPostulation" in offer:
                        office.website = offer["contact"]["urlPostulation"]
                    elif "urlRecruteur" in offer:
                        office.website = offer["contact"]["urlRecruteur"]

        self.office_count = len(offices)
        return offices

    def get_offers_for_romes(self, romes):
        offers = []

        for romes_batch in chunks(romes, OFFRES_ESD_MAXIMUM_ROMES):
            url = OFFRES_ESD_ENDPOINT_URL
            params = {
                "range": "0-{}".format(OFFRES_ESD_MAXIMUM_PAGE_SIZE - 1),
                "sort": 1,
                "codeROME": ",".join(romes_batch),
                "natureContrat": ",".join(self.get_contract_nature_codes()),
                "commune": self.commune_id,
                "distance": min(self.distance, OFFRES_ESD_MAXIMUM_DISTANCE),
            }
            response = esd.get_response(url, params)
            # Convenient reminder to dump json to file for test mockups.
            # json.dump(response, json_file, sort_keys=True, indent=4)
            offers += response["resultats"]

        return offers
