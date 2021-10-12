from labonneboite.conf import settings
from labonneboite.common import esd

ENDPOINT_URL = "%s/partenaire/peconnect-competences/v2/competences" % settings.PEAM_API_BASE_URL

def get_user_info(current_user):
    params = {
        'commune': '',
    }
    response = esd.get_response(ENDPOINT_URL, params)
    return response['resultats']

