"""
Useful functions to be used in mock backends.
"""

import json
from unittest import mock


def mock_response_from_json(file):
    """
    Mock an HTTP request based on a JSON file.
    Return a 200 status code and the response.
    """
    response = mock.Mock(status_code=200, json=mock.Mock(return_value=json.loads(file)))
    return mock.Mock(return_value=response)
