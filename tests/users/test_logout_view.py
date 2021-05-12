import json
import unittest

from app import app, db
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime_one_hour_ahead


class TestUserLogoutView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        user = Users(
            Name="UnitTest User",
            Username="unittest",
            Password="password"
        )
        db.session.add(user)
        db.session.commit()
        self.user_id = user.UserID

        # This is non-standard, but is fine for testing.
        self.access_token = "unittest-access-token"
        user_token = UsersAccessTokens(
            UserID=user.UserID,
            AccessToken=self.access_token,
            ExpirationDate=get_datetime_one_hour_ahead()
        )
        db.session.add(user_token)
        db.session.commit()

        # Define level for admin
        if not UsersAccessLevels.query.filter_by(LevelName="Admin").first():
            access_level = UsersAccessLevels(
                UsersAccessLevelID=4,
                LevelName="Admin"
            )
            db.session.add(access_level)
            db.session.commit()

        grant_admin = UsersAccessMapping(
            UserID=user.UserID,
            UsersAccessLevelID=4
        )
        db.session.add(grant_admin)
        db.session.commit()

    def tearDown(self):
        delete_user = Users.query.filter(Users.Name.like("UnitTest%")).all()
        for user in delete_user:
            db.session.delete(user)

        access = UsersAccessLevels.query.filter_by(LevelName="Admin").first()
        db.session.delete(access)

        db.session.commit()

    def test_logging_out_with_valid_user_and_token(self):
        """Should logout."""
        response = self.app.post(
            "/api/1.0/logout/",
            data=None,
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertTrue(data["success"])

    def test_logging_out_with_invalid_user_and_valid_token(self):
        """Should return a not found response. Even if the UserID is valid but Token is invalid, or
        the other way around. We don't want to expose too much information in the API."""
        response = self.app.post(
            "/api/1.0/logout/",
            data=None,
            headers={
                'User': -1,
                'Authorization': self.access_token
            }
        )
        data = json.loads(response.data.decode())

        self.assertEqual(404, response.status_code)
        self.assertNotEqual(None, data)
        self.assertFalse(data["success"])

    def test_logging_out_with_valid_user_and_invalid_token(self):
        """This is allowed, in case the user's access token has somehow corrupted, but they still
        want to log out. It will delete all access (including old ones), so it should be safe."""
        response = self.app.post(
            "/api/1.0/logout/",
            data=None,
            headers={
                'User': self.user_id,
                'Authorization': "bogus"
            }
        )
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertTrue(data["success"])

    def test_logging_out_with_invalid_user_and_invalid_token(self):
        """Should return a 404, since the user does not exist."""
        response = self.app.post(
            "/api/1.0/logout/",
            data=None,
            headers={
                'User': "hello",
                'Authorization': "bogus"
            }
        )
        data = json.loads(response.data.decode())

        self.assertEqual(404, response.status_code)
        self.assertNotEqual(None, data)
        self.assertFalse(data["success"])
        self.assertEqual("Missing UserID or Token", data["error"])
