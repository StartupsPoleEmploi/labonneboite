import json
import unittest
import unittest.mock

from labonneboite.common import activity


class ActivityTests(unittest.TestCase):

    def test_log_from_anonymous_user(self):
        with unittest.mock.patch.object(activity.logger, 'info') as logger:
            activity.log('testevent', somekey='somevalue')
            log_data = json.loads(logger.call_args[0][0])

            logger.assert_called_once()
            self.assertEqual('testevent', log_data['nom'])
            self.assertIn('proprietes', log_data)
            self.assertEqual(None, log_data['idutilisateur'])
            self.assertEqual(None, log_data['idutilisateur-peconnect'])
            self.assertEqual({'somekey': 'somevalue'}, log_data['proprietes'])
