from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common.database import db_session
from labonneboite.common.models import User, OfficeAdminAdd, OfficeAdminRemove,\
    OfficeAdminUpdate, Office
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect
from labonneboite.web.admin.views.office_admin_remove import OfficeAdminRemoveModelView


class AdminTest(DatabaseTest):

    def setUp(self, *args, **kwargs):
        super(AdminTest, self).setUp(*args, **kwargs)

        self.user = User(email='john@doe.com', gender='male', first_name='John', last_name='Doe')
        db_session.add(self.user)
        db_session.flush()

        # Required for `self.logout` to work which looks for the `extra_data` attribute.
        user_social_auth = UserSocialAuth(
            provider=PEAMOpenIdConnect.name,
            extra_data={'id_token': 'fake'},
            user_id=self.user.id,
        )
        db_session.add(user_social_auth)
        db_session.commit()

        self.office1 = Office(
            siret="78548035101646",
            company_name="SUPERMARCHES MATCH",
            office_name="SUPERMARCHES MATCH",
            naf="4711D",
            street_number="45",
            street_name="AVENUE ANDRE MALRAUX",
            city_code="57463",
            zipcode="57000",
            email="supermarche@match.com",
            tel="0387787878",
            website="http://www.supermarchesmatch.fr",
            flag_alternance=0,
            flag_junior=0,
            flag_senior=0,
            flag_handicap=0,
            departement="57",
            headcount="12",
            hiring=90,
            score_alternance=90,
            x=6.17952,
            y=49.1044,
        )
        self.office1.save()

        self.assertEqual(Office.query.count(), 1)
        self.assertEqual(db_session.query(User).count(), 1)

    def test_admin_access(self):
        """
        Test admin access permissions.
        """

        admin_urls = [
            self.url_for('admin.index'),
            self.url_for('users.index_view'),
            self.url_for('officeadminadd.index_view'),
            self.url_for('officeadminremove.index_view'),
            self.url_for('officeadminupdate.index_view'),
            self.url_for('officeadminextrageolocation.index_view'),
        ]

        db_session.query(User).update({User.active: True, User.is_admin: False})
        db_session.commit()
        self.user = db_session.query(User).filter_by(id=self.user.id).first()
        with self.login_client.test_client(user=self.user) as client:

            for url in admin_urls:

                # Access should be denied when a user is not logged in.
                db_session.query(User).update({User.active: True, User.is_admin: False})
                db_session.commit()
                self.user = db_session.query(User).filter_by(id=self.user.id).first()
                self.assertTrue(self.user.active)
                self.assertFalse(self.user.is_admin)
                rv = client.get(url)
                self.assertEqual(rv.status_code, 404)

                # Access should be denied when a user is logged in but is not an admin.
                rv = client.get(url)
                self.assertEqual(rv.status_code, 404)

                # Access should be granted when a user is logged in and is admin.
                db_session.query(User).update({User.active: True, User.is_admin: True})
                db_session.commit()
                self.user = db_session.query(User).filter_by(id=self.user.id).first()
                self.assertTrue(self.user.active)
                self.assertTrue(self.user.is_admin)

                rv = client.get(url)
                self.assertEqual(rv.status_code, 200)

                # Access should be denied when a user is not active.
                db_session.query(User).update({User.active: False, User.is_admin: True})
                db_session.commit()
                self.user = db_session.query(User).filter_by(id=self.user.id).first()
                self.assertFalse(self.user.active)
                self.assertTrue(self.user.is_admin)
                rv = client.get(url)
                self.assertEqual(rv.status_code, 404)

    def test_admin_office_remove(self):
        """
        Test `OfficeAdminRemoveModelView.after_model_change()` to delete an office
        in OfficeAdminUpdate and OfficeAdminAdd
        """

        office_to_remove = OfficeAdminRemove(
            siret=self.office1.siret,
            name=self.office1.company_name,
        )
        office_to_add = OfficeAdminAdd(
            siret=self.office1.siret,
            company_name=self.office1.company_name,
            office_name="GEP",
            naf="4772A",
            zipcode="57000",
            city_code="57463",
            departement="57",
            hiring=80,
            x=6.17528,
            y=49.1187,
        )
        office_to_update = OfficeAdminUpdate(
            sirets=self.office1.siret,
            name=self.office1.name,
            new_company_name="New raison sociale",
            new_office_name="New enseigne",
            new_email="foo@pole-emploi.fr",
            new_phone="",  # Leave empty on purpose: it should not be modified.
            new_website="https://foo.pole-emploi.fr",
        )
        office_to_update.save()
        office_to_add.save()
        office_to_remove.save()

        self.assertEqual(OfficeAdminRemove.query.count(), 1)
        self.assertEqual(OfficeAdminAdd.query.count(), 1)
        self.assertEqual(OfficeAdminUpdate.query.count(), 1)

        view = OfficeAdminRemoveModelView(OfficeAdminRemove, db_session)
        view.after_model_change(None, office_to_remove, False)

        self.assertEqual(OfficeAdminAdd.query.count(), 0)
        self.assertEqual(OfficeAdminUpdate.query.count(), 0)
        self.assertEqual(Office.query.count(), 0)
