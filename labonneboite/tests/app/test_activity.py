import json
import unittest
import unittest.mock

from labonneboite.common import activity


class ActivityTests(unittest.TestCase):

    def test_log_from_anonymous_user(self):
        with unittest.mock.patch.object(activity.userLogger, 'info') as logger:
            activity.log('testevent', somekey='somevalue')
            log_data = json.loads(logger.call_args[0][0])

            logger.assert_called_once()
            self.assertEqual('testevent', log_data['nom'])
            self.assertIn('proprietes', log_data)
            self.assertEqual(None, log_data['idutilisateur'])
            self.assertEqual(None, log_data['idutilisateur-peconnect'])
            self.assertEqual({'somekey': 'somevalue'}, log_data['proprietes'])

    def test_log_api(self):
        with unittest.mock.patch.object(activity.apiLogger, 'info') as logger:
            activity.log_api(200, 'app test', 'user test', 'referrer test', 'remote address test')
            log_data = json.loads(logger.call_args[0][0])

            logger.assert_called_once()
            self.assertIn('requestId', log_data)
            self.assertIn('date', log_data)
            self.assertEqual(200, log_data['status'])
            self.assertEqual('app test', log_data['application'])
            self.assertEqual('user test', log_data['httpUserAgent'])
            self.assertEqual('referrer test', log_data['httpReferer'])
