from unittest.mock import patch, MagicMock
from main import app
import unittest


class TestTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()

    def test_index(self):
        response = self.client.get('/')


        # then
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please, use /hello endpoint to start.", response.text)


    def test_hello(self):
        response = self.client.get('/hello')


        # then
        self.assertEqual(401, response.status_code)
        self.assertIn("Please, send me your email as `email` GET parameter so we could start", response.text)



if __name__ == '__main__':
    unittest.main()
