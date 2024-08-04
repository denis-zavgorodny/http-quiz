from unittest.mock import patch, MagicMock

import jwt
from dotenv import dotenv_values

from main import app
import unittest

config = dotenv_values("../.env")

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

    def test_hello_with_email(self):
        mail = "some@email.com"
        d = config.get("SECRET")

        response = self.client.get(f"/hello?email={mail}")
        secret = jwt.encode({"email": mail, "step": "/hello"}, config.get("SECRET"), algorithm='HS256')
        # then
        self.assertEqual(200, response.status_code)
        self.assertIn("Your next mission is to send me this token in HTTP header `x-secret` back to endpoint "
                      "`/mission1`.", response.text)

        self.assertIn(secret, response.text)



if __name__ == '__main__':
    unittest.main()
