import json
import unittest

from datetime import datetime

from app import app, db
from apps.users.models import Users, UsersAccessTokens
from apps.utils.time import get_datetime


class TestRefreshTokenView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # Create a user
        user = Users(
            Name="UnitTest User",
            Username="unittest",
            Password="password"
        )
        db.session.add(user)
        db.session.commit()
        self.user_id = user.UserID

        # Create a valid token for the user
        # This is non-standard, but is fine for testing.
        self.access_token = "unittest-access-token"
        self.refresh_token = "unittest-refresh-token"
        user_token = UsersAccessTokens(
            UserID=user.UserID,
            AccessToken=self.access_token,
            RefreshToken=self.refresh_token,
            ExpirationDate=get_datetime()
        )
        db.session.add(user_token)
        db.session.commit()

    def tearDown(self):
        user = Users.query.filter_by(UserID=self.user_id).first()
        db.session.delete(user)
        db.session.commit()

    def test_refresh_with_valid_details(self):
        """When a valid UserID and RefreshToken are given, we should get a new AccessToken that is
        valid for 1 hour from "now"."""
        response = self.app.post(
            "/api/1.0/refresh/",
            data=None,
            headers={
                'User': self.user_id,
                'Authorization': self.refresh_token
            }
        )

        token = UsersAccessTokens.query.filter_by(UserID=self.user_id).all()

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(token))
        self.assertNotEqual(self.access_token, token[0].AccessToken)
        self.assertTrue(len(token[0].RefreshToken) > 0)
        self.assertEqual(self.user_id, token[0].UserID)
        self.assertTrue(datetime.now() < token[0].ExpirationDate)
        self.assertEqual(self.refresh_token, token[0].RefreshToken)

    def test_refresh_with_invalid_details(self):
        """When an invalid UserID or RefreshToken are given, we should get a 404 response."""
        response = self.app.post(
            "/api/1.0/refresh/",
            data=None,
            headers={
                'User': "fake",
                'Authorization': "wrong"
            }
        )
        data = json.loads(response.data.decode())

        token = UsersAccessTokens.query.filter_by(UserID=self.user_id).all()

        self.assertEqual(404, response.status_code)
        self.assertNotEqual(None, data)
        self.assertFalse(data["success"])
        self.assertEqual("Missing UserID or valid Token", data["error"])

        self.assertEqual(1, len(token))
        self.assertTrue(len(token[0].RefreshToken) > 0)
        self.assertFalse(datetime.now() < token[0].ExpirationDate)
