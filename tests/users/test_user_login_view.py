import json
import unittest

from werkzeug.security import generate_password_hash

from app import app, db
from apps.users.models import Users, UsersAccessTokens
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestUserLoginView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        user1 = Users(
            Name="UnitTest",
            Username="unittester",
            Password=generate_password_hash("unittest"),
            Created=get_datetime(),
        )
        user2 = Users(
            Name="UnitTest2",
            Username="unittester2",
            Password=generate_password_hash("unittest2"),
            Created=get_datetime(),
        )
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # This is non-standard, but is fine for testing.
        self.access_token = "unittest-access-token"
        user_token = UsersAccessTokens(
            UserID=user1.UserID,
            AccessToken=self.access_token,
            ExpirationDate=get_datetime_one_hour_ahead()
        )
        db.session.add(user_token)
        db.session.commit()

        self.valid_users = [user1.UserID, user2.UserID]

    def tearDown(self):
        delete_user = Users.query.filter(Users.Name.like("UnitTest%")).all()
        for user in delete_user:
            db.session.delete(user)

        db.session.commit()

    def test_logging_in_with_valid_user_and_password(self):
        """Should login for 1 hour and return the Tokens in the response."""
        response = self.app.post(
            "/api/1.0/login/",
            data=json.dumps(
                dict(
                    username="unittester",
                    password="unittest",
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        self.assertEqual(201, response.status_code)
        self.assertNotEqual(None, data)
        self.assertTrue(data["success"])
        self.assertEqual(36, len(data["accessToken"]))
        self.assertEqual(36, len(data["refreshToken"]))
        self.assertEqual(3600, data["expires_in"])

    def test_logging_in_with_valid_user_and_password_and_existing_old_token_in_db(self):
        """Should login, and also should remove the old token since it is unusable anyway."""
        response = self.app.post(
            "/api/1.0/login/",
            data=json.dumps(
                dict(
                    username="unittester",
                    password="unittest",
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        # Old token should not exist anymore
        old_token = UsersAccessTokens.query.filter_by(AccessToken="unittest-access-token").first()

        self.assertEqual(201, response.status_code)
        self.assertNotEqual(None, data)
        self.assertTrue(data["success"])
        self.assertEqual(36, len(data["accessToken"]))
        self.assertEqual(36, len(data["refreshToken"]))
        self.assertEqual(3600, data["expires_in"])
        self.assertEqual(old_token, None)

    def test_logging_in_with_valid_user_and_wrong_password(self):
        """Should return a 401 with error message."""
        response = self.app.post(
            "/api/1.0/login/",
            data=json.dumps(
                dict(
                    username="unittester",
                    password="doesnot",
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        self.assertEqual(401, response.status_code)
        self.assertNotEqual(None, data)
        self.assertFalse(data["success"])
        self.assertFalse("accessToken" in data)
        self.assertFalse("refreshToken" in data)
        self.assertEqual("Invalid password.", data["error"])

    def test_logging_in_with_invalid_user_and_password(self):
        """Should return a 404, since the user does not exist."""
        response = self.app.post(
            "/api/1.0/login/",
            data=json.dumps(
                dict(
                    username="nope",
                    password="doesnot",
                )
            ),
            content_type="application/json"
        )

        self.assertEqual(404, response.status_code)
