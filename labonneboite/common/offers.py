# coding: utf8
import json
from collections import defaultdict
from labonneboite.conf import settings
from labonneboite.common.models import Office
from labonneboite.common.fetcher import Fetcher
from labonneboite.common.load_data import OGR_ROME_CODES
from labonneboite.common import hiring_type_util
from labonneboite.common import esd
from sqlalchemy import tuple_, or_


OFFRES_ESD_ENDPOINT_URL = "%s/partenaire/offresdemploi/v1/rechercheroffres" % settings.PEAM_API_BASE_URL

OFFRES_ESD_MAXIMUM_PAGE_SIZE = 150
OFFRES_ESD_MAXIMUM_DISTANCE = 200

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


    def get_offices(self):
        offers = []
        for rome in self.romes:
            offers += self.get_offers_for_rome(rome)

        # To identify the office of a given offer, as siret is absent in offers data,
        # we instead use the couple (company_name, departement) in the offer's data.
        # It will matched to an office either on (company_name, departement)
        # or on (office_name, departement).
        # Let's group offers by their parent office using this office_key. 
        office_key_to_offers = defaultdict(list)
        for offer in offers:
            if 'departmentCode' in offer and 'companyName' in offer:
                office_key = (offer['departmentCode'], offer['companyName'])
                office_key_to_offers[office_key].append(offer)

        # Fetch matching offices from db. Offers without a match
        # will silently be dropped.
        offices = Office.query.filter(
            or_(
                tuple_(Office.departement, Office.company_name).in_(
                    office_key_to_offers.keys()
                ),
                tuple_(Office.departement, Office.office_name).in_(
                    office_key_to_offers.keys()
                ),                
            )
        ).limit(self.page_size).all()

        # Add extra fields to each office to enrich the API JSON response.
        # - `distance` : distance between the office and the search location, same as
        #                in a regular hidden market search.
        # - `offer_count` and `offers` : useful minimalistic information about the offers found
        #                for this office.
        for office in offices:
            office_possible_keys = [
                (office.departement, office.company_name),
                (office.departement, office.office_name),
            ]
            first_offer = None

            for office_key in office_possible_keys:
                if office_key in office_key_to_offers:
                    office_offers = office_key_to_offers[office_key]
                    first_offer = office_offers[0]
                    break
                    
            if first_offer is not None:
                office.distance = first_offer['distance']
                office.matched_rome = OGR_ROME_CODES[first_offer['romeProfessionCode']]
                office.offers_count = len(office_offers)
                office.offers = [{'url': offer['origins'][0]['originUrl']} for offer in office_offers]
                for offer in office_offers:
                    if 'companyContactEmail' in offer:
                        office.email = offer['companyContactEmail']
                    if 'companyContactPhone' in offer:
                        office.tel = offer['companyContactPhone']
                    if 'companyUrl' in offer:
                        office.website = offer['companyUrl']

        # Only keep offices which actually matched an offer.
        offices = [office for office in offices if hasattr(office, 'offers_count')]

        self.office_count = len(offices)
        return offices


    def get_offers_for_rome(self, rome):
        response = esd.get_response(
            url=OFFRES_ESD_ENDPOINT_URL,
            data=json.dumps(self.get_data(rome)),
        )
        offers = response['results']
        return offers


    def get_data(self, rome):
        data_json = {
          "technicalParameters" : {
            "page": 1,
            "per_page": OFFRES_ESD_MAXIMUM_PAGE_SIZE,
            "sort": 2
          },
          "criterias" : {
            "cityCode": self.commune_id,
            "romeProfessionCardCode": rome,
            "cityDistance": min(self.distance, OFFRES_ESD_MAXIMUM_DISTANCE),
            "contractNatureCode": self.get_contract_nature_codes()
          }
        }
        return data_json
