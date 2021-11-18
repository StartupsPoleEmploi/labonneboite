from typing import Union
import requests


class PEIOGetterBase:
    url: str
    method: Union["GET", "POST"] = "GET"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def create_header(self):
        return {'Authorization': f'Bearer {self.access_token}'}

    def fetch(self):
        response = requests.request(
            self.method,
            self.url,
            params={
                'realm': '/individu'
            },
            headers=self.create_header(),
        )
        response.raise_for_status()
        return response.json()
