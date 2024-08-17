from pathlib import Path
from unittest.mock import patch, MagicMock

import jwt
from dotenv import dotenv_values

from main import app
import unittest

config = dotenv_values(Path(__file__).parent.parent / ".env")

class TestTasks(unittest.TestCase):
    _mail = "some@email.com"

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
        response = self.client.get(f"/hello?email={self._mail}")
        secret = jwt.encode({"email": self._mail, "step": "/hello"}, config.get("SECRET"), algorithm='HS256')
        # then
        self.assertEqual(200, response.status_code)
        self.assertIn("Your next mission is to send me this token in HTTP header `x-secret` back to endpoint "
                      "`/mission1`.", response.text)

        self.assertIn(secret, response.text)

    @patch('main.random')
    def test_mission1(self, mocked_random):
        mocked_random.randint.return_value = "10"
        secret = jwt.encode({"email": self._mail, "step": "/hello"}, config.get("SECRET"), algorithm='HS256')
        response_secret = jwt.encode({
            "email": self._mail,
            "step": "/mission1",
            "first_number": "10",
            "second_number": "10"
        }, config.get("SECRET"), algorithm='HS256')

        response = self.client.get(f"/mission1", headers={"x-secret": secret})

        # then
        self.assertEqual(200, response.status_code)
        self.assertIn("Then please, add those two numbers and send me the result back", response.text)
        self.assertIn("to the endpoint `/mission2`", response.text)

        self.assertIn(response_secret, response.text)
        self.assertEqual([
            "first_number=10; Path=/",
            "second_number=10; Path=/"
        ], response.headers.get_all("Set-Cookie"))

    def test_mission1_wrong_step(self):
        secret = jwt.encode({"email": self._mail, "step": "/some"}, config.get("SECRET"), algorithm='HS256')

        response = self.client.get(f"/mission1", headers={"x-secret": secret})

        # then
        self.assertEqual(200, response.status_code)
        self.assertIn("You need to finish previous step. Please visit `/hello`", response.text)

    def test_mission1_no_header(self):
        response = self.client.get(f"/mission1")

        # then
        self.assertEqual(401, response.status_code)
        self.assertIn("You need to pass a valid non-empty token as `x-secret` header", response.text)


    def test_mission2_no_header(self):
        secret = jwt.encode({
            "email": self._mail,
            "step": "/mission1",
            "first_number": "10",
            "second_number": "10"
        }, config.get("SECRET"), algorithm='HS256')
        response = self.client.get(f"/mission2", headers={"x-secret": secret})

        # then
        self.assertEqual(200, response.status_code)
        self.assertIn("I can not find cookie with name `result` in your request", response.text)

    def test_mission2_with_header(self):
        secret = jwt.encode({
            "email": self._mail,
            "step": "/mission1",
            "first_number": "10",
            "second_number": "10"
        }, config.get("SECRET"), algorithm='HS256')

        self.client.set_cookie("result", "20")

        response_secret = jwt.encode({
            "email": self._mail,
            "step": "/mission2",
        }, config.get("SECRET"), algorithm='HS256')

        response = self.client.get(f"/mission2", headers={"x-secret": secret})

        # then
        self.assertEqual(200, response.status_code)
        self.assertIn("Cool. The result is 20. Well done!", response.text)
        self.assertIn(response_secret, response.text)



if __name__ == '__main__':
    unittest.main()
