from social_flask.utils import load_strategy

from labonneboite.web.auth.backends import peam
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common.models import User


class AuthPipelineTest(DatabaseTest):

    def setUp(self):
        super().setUp()
        self.response = {
            'access_token': 'access-token',
            'email': 'my@email.com',
            'expires_in': 1000,
            'given_name': 'ELTON',
            'family_name': 'JOHN',
            'gender': 'male',
            'id_token': 'loooooooongstring',
            'nonce': 'longnonce',
            'refresh_token': 'refresh-token',
            'scope': 'application_PAR_lbb_scope email api_peconnect-individuv1 openid profile',
            'sub': 'peconnect-userid',
            'token_type': 'Bearer',
            'updated_at': '0'
        }

    def run_pipeline(self, BackendClass):
        with self.test_request_context():
            strategy = load_strategy()
            backend = BackendClass(strategy=strategy)
            pipeline = strategy.get_pipeline(backend)
            result = backend.run_pipeline(
                pipeline, pipeline_index=0,
                backend=backend,
                is_new=False,
                response=self.response,
                storage=strategy.storage,
                strategy=strategy,
                user=None
            )
            return result

    def test_run_pipeline_with_PEAMOpenIdConnect(self):
        result = self.run_pipeline(peam.PEAMOpenIdConnect)
        self.assertIn('user', result)

    def test_run_pipeline_with_user_email_change(self):
        user = User(email='preexisting@email.com', external_id='peconnect-userid')
        user.save()
        self.assertEqual(
            User.query.filter_by(external_id='peconnect-userid').first().email,
            'preexisting@email.com',
        )
        self.run_pipeline(peam.PEAMOpenIdConnect)
        self.assertEqual(
            User.query.filter_by(external_id='peconnect-userid').first().email,
            'my@email.com',
        )

    def test_run_pipeline_with_PEAMOpenIdConnectNoPrompt(self):
        result = self.run_pipeline(peam.PEAMOpenIdConnectNoPrompt)
        self.assertIn('user', result)

    def test_run_pipeline_twice(self):
        result1 = self.run_pipeline(peam.PEAMOpenIdConnect)
        result2 = self.run_pipeline(peam.PEAMOpenIdConnectNoPrompt)
        self.assertEqual(result1['user'].id, result2['user'].id)

    def test_run_pipeline_with_missing_required_field(self):
        self.response.pop('email')
        self.assertRaises(peam.AuthFailedMissingReturnValues, self.run_pipeline, peam.PEAMOpenIdConnect)

    def test_run_pipeline_with_empty_required_field(self):
        self.response['email'] = ''
        self.assertRaises(peam.AuthFailedMissingReturnValues, self.run_pipeline, peam.PEAMOpenIdConnect)
