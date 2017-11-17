import logging
import requests

from labonneboite.conf import settings

logger = logging.getLogger(__name__)

# API documentation: https://google-developers.appspot.com/maps/documentation/distance-matrix/intro
DISTANCE_MATRIX_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json'


def durations(origin, destinations):
    return list(iter_durations(origin, destinations))

def iter_durations(origin, destinations):
    """
    Fetch travel durations 10 by 10.
    """
    # We specify the precision to make sure geo coordinates are not rounded
    coordinate_format = '{:.7f},{:.7f}'
    # TODO shouldn't we specify a time of departure?
    params = {
        'origins': [coordinate_format.format(origin[0], origin[1])],
        'key': settings.GOOGLE_API_KEY
    }

    for i in range(0, len(destinations), 10):
        batch = destinations[i:i+10]
        params['destinations'] = '|'.join([
            coordinate_format.format(lat, lon) for (lat, lon) in batch
        ])
        # TODO no timeout here?
        response = requests.get(DISTANCE_MATRIX_URL, params=params)

        if response.status_code >= 400:
            logger.warning('Google API %d response: "%s"', response.status_code, response.content)
            for _ in batch:
                yield None
        else:
            # TODO check status code: if != 200, log warning, skip
            for element in response.json()['rows'][0]['elements']:
                # TODO check that element is not {'status': 'ZERO_RESULTS'} (status should be 'OK')
                if 'duration' in element:
                    duration = element['duration']['value']
                else:
                    duration = None
                yield duration
