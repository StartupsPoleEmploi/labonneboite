import typing as t
from abc import ABC, abstractmethod

from labonneboite.tests.test_base import DatabaseTest

from .....common.models import Office

if t.TYPE_CHECKING:  # pragma: no cover
    from flask.testing import FlaskClient
    from werkzeug.test import TestResponse


def create_office(**kwargs):
    office_kwargs = dict(
        siret="78548035101647",
        company_name="HYPER U",
        naf="4711D",
        city_code="44101",
        zipcode="44620",
        departement="44",
        headcount="21",
        x=-1.68333,
        y=47.183331,
    )
    office_kwargs.update(kwargs)
    return Office(**office_kwargs)


class BaseTest(ABC):
    app: "FlaskClient"

    @abstractmethod
    def url_for(self, endpoint, **kwargs) -> str:
        pass

    def call(self, email: str):
        response: "TestResponse" = self.app.get(
            self.url_for("data.sirets_for_email"),
            query_string={"email": email}
        )
        return response


class TestEmpty(BaseTest, DatabaseTest):
    def test_not_found(self):
        response = self.call("invalid@example.com")
        self.assertEqual(404, response.status_code)

    def test_invalid_email(self):
        self.url_for
        response = self.call("invalid")
        self.assertEqual(400, response.status_code)


class TestNoHiring(BaseTest, DatabaseTest):
    def setUp(self):
        super().setUp()
        self.office = create_office(email="valid@example.com", hiring=0)
        self.office.save()

    def tearDown(self):
        self.office.delete()
        super().tearDown()

    def test_not_found(self):
        response = self.call("valid@example.com")
        self.assertEqual(404, response.status_code)


class TestValid(BaseTest, DatabaseTest):
    def setUp(self):
        super().setUp()
        self.office = create_office(email="valid@example.com", hiring=1)
        self.office.save()

    def tearDown(self):
        self.office.delete()
        super().tearDown()

    def test_not_found(self):
        response = self.call("valid@example.com")
        self.assertEqual(200, response.status_code)
