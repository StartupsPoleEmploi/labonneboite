from labonneboite.tests.test_base import AppTest


class RootTest(AppTest):

    def test_kit(self):
        rv = self.app.get(self.url_for('root.kit'))
        # Non-empty pdf file
        self.assertEqual('application/pdf', rv.content_type)
        self.assertLess(1000, rv.content_length)
