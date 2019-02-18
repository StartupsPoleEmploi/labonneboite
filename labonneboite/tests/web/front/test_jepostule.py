from unittest import mock, TestCase

from labonneboite.web.jepostule import views
from labonneboite.web.jepostule import utils


class JePostuleTests(TestCase):

    def test_get_token(self):
        mock_response = mock.Mock(
            status_code=200,
            json=mock.Mock(
                return_value={
                    'token': 'apptoken',
                    'timestamp': 123,
                }
            )
        )
        with mock.patch.object(views.requests, 'post', return_value=mock_response) as mock_post:
            token, timestamp = views.get_token(client_id="client_id", client_secret="secret")

            mock_post.assert_called_once()
            self.assertEqual('apptoken', token)
            self.assertEqual(123, timestamp)

    def test_get_token_401(self):
        mock_response = mock.Mock(
            status_code=401,
            content='Error message',
            json=mock.Mock(
                side_effect=ValueError,
            )
        )
        with mock.patch.object(views.requests, 'post', return_value=mock_response) as mock_post:
            self.assertRaises(views.JePostuleError, views.get_token, client_id="client_id", client_secret="secret")
            mock_post.assert_called_once()

    def test_valid_email(self):
        self.assertTrue(utils.is_valid_email("patron@macdonalds.com"))
        self.assertFalse(utils.is_valid_email("patron@macdonald's.com"))
