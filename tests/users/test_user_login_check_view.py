import json
import unittest
import uuid

from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app import app, db
from apps.users.models import Users, UsersAccessTokens
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestUserLoginCheckView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        user = Users(
            Name="UnitTest",
            Username="unittester",
            Password=generate_password_hash("unittest"),
            Created=get_datetime(),
        )
        db.session.add(user)
        db.session.commit()
        self.user_id = user.UserID
        self.valid_access_token = str(uuid.uuid4())
        self.valid_refresh_token = str(uuid.uuid4())
        token = UsersAccessTokens(
            UserID=user.UserID,
            AccessToken=self.valid_access_token,
            RefreshToken=self.valid_refresh_token,
            ExpirationDate=get_datetime_one_hour_ahead(),
        )
        db.session.add(token)
        db.session.commit()

    def tearDown(self):
        user = Users.query.filter_by(Name="UnitTest").first()
        db.session.delete(user)
        db.session.commit()

    def test_checking_with_valid_token(self):
        """With a valid token, should simply respond with confirmation."""
        response = self.app.post(
            "/api/1.0/login/check/",
            data=json.dumps(
                dict(
                    id=self.user_id,
                    access_token=self.valid_access_token,
                    refresh_token=self.valid_refresh_token,
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(data, {
            "success": True,
            "message": "AccessToken is valid",
        })

    def test_checking_with_expired_token(self):
        """With an expired token, should generate a fresh one and return it."""
        expired = UsersAccessTokens.query.filter_by(UserID=self.user_id).first()
        expired.ExpirationDate = datetime.now() - timedelta(hours=2)
        db.session.commit()

        response = self.app.post(
            "/api/1.0/login/check/",
            data=json.dumps(
                dict(
                    id=self.user_id,
                    access_token=self.valid_access_token,
                    refresh_token=self.valid_refresh_token,
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())
        token = UsersAccessTokens.query.filter_by(UserID=self.user_id).first()

        self.assertEquals(200, response.status_code)
        self.assertEquals(data, {
            "success": True,
            "accessToken": token.AccessToken,
            "message": "AccessToken has been renewed",
            "expires_in": 3600,
        })

    def test_checking_with_invalid_token(self):
        """With an invalid token, should return 401."""
        response = self.app.post(
            "/api/1.0/login/check/",
            data=json.dumps(
                dict(
                    id=self.user_id,
                    access_token=self.valid_access_token,
                    refresh_token=str(uuid.uuid4()),
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        self.assertEquals(401, response.status_code)
        self.assertEquals(data, {
            "success": False,
            "error": "invalid_token",
        })
