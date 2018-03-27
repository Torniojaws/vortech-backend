import json
import unittest

from flask_caching import Cache
from werkzeug import check_password_hash

from app import app, db
from apps.users.models import Users, UsersAccessLevels, UsersAccessMapping, UsersAccessTokens
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead
from settings.config import CONFIG


class TestUsersView(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        user1 = Users(
            Name="UnitTest",
            Username="unittester",
            Password="unittest",
            Created=get_datetime(),
        )
        user2 = Users(
            Name="UnitTest2",
            Username="unittester2",
            Password="unittest2",
            Created=get_datetime(),
        )
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # Make user1 a registered user with a token
        if not UsersAccessLevels.query.filter_by(LevelName="Registered").first():
            registered = UsersAccessLevels(
                UsersAccessLevelID=2,
                LevelName="Registered"
            )
            db.session.add(registered)
            db.session.commit()

        grant_registered = UsersAccessMapping(
            UserID=user1.UserID,
            UsersAccessLevelID=2
        )

        self.access_token = "unittest-access-token"
        user_token = UsersAccessTokens(
            UserID=user1.UserID,
            AccessToken=self.access_token,
            ExpirationDate=get_datetime_one_hour_ahead()
        )

        db.session.add(grant_registered)
        db.session.add(user_token)
        db.session.commit()

        self.valid_users = [user1.UserID, user2.UserID]

        # We also need a valid admin user for the add release endpoint test.
        user = Users(
            Name="UnitTest Admin",
            Username="unittest",
            Password="password"
        )
        db.session.add(user)
        db.session.commit()

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

        self.user_id = user.UserID

    def tearDown(self):
        delete_user = Users.query.filter(Users.Name.like("UnitTest%")).all()
        for u in delete_user:
            db.session.delete(u)
        db.session.commit()

    def test_getting_one_user(self):
        """Should return just one user's details. NB: This needs a registered user."""
        resp = self.app.get(
            "/api/1.0/users/{}".format(self.valid_users[0]),
            headers={
                'User': self.valid_users[0],
                'Authorization': self.access_token
            }
        )
        user = json.loads(resp.get_data().decode())

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(1, len(user["users"]))
        self.assertEquals("unittester", user["users"][0]["username"])
        self.assertFalse("password" in user["users"][0])  # Should not be included
        self.assertEquals(2, user["users"][0]["level"])

    def test_getting_all_users(self):
        """Should return all users' details."""
        resp = self.app.get("/api/1.0/users/")
        user = json.loads(resp.get_data().decode())

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(3, len(user["users"]))
        self.assertEquals("unittester", user["users"][0]["username"])
        self.assertEquals("UnitTest2", user["users"][1]["name"])
        self.assertFalse("password" in user["users"][0])  # Should not be included
        self.assertFalse("password" in user["users"][1])  # Should not be included
        self.assertEquals(CONFIG.REGISTERED_LEVEL, user["users"][0]["level"])
        # This user is not mapped (exceptional case), so it should have guest level
        self.assertEquals(CONFIG.GUEST_LEVEL, user["users"][1]["level"])

    def test_adding_user(self):
        """The user should be created and the password must be in hashed form. Note that all
        communication happens via HTTPS in the production server."""
        resp = self.app.post(
            "/api/1.0/users/",
            data=json.dumps(
                dict(
                    name="UnitTest Post",
                    email="unittest@example.com",
                    username="UnitTester",
                    password="unittesting",
                )
            ),
            content_type="application/json"
        )

        user = Users.query.filter_by(Name="UnitTest Post").first_or_404()
        userlevel = UsersAccessMapping.query.filter_by(UserID=user.UserID).first()

        self.assertEquals(resp.status_code, 201)
        self.assertTrue("Location" in resp.get_data().decode())
        self.assertEquals("UnitTest Post", user.Name)
        self.assertEquals("unittest@example.com", user.Email)
        self.assertFalse(user.Password == "unittesting")  # Must not be the cleartext password
        # The hashed password must validate against the real cleartext password
        self.assertTrue(check_password_hash(user.Password, "unittesting"))
        # Sanity check with invalid password
        self.assertFalse(check_password_hash(user.Password, "notcorrect"))
        # Make sure user is mapped as level 2 (Registered user)
        self.assertNotEquals(None, userlevel)
        self.assertEquals(2, userlevel.UsersAccessLevelID)

    def test_adding_user_with_empty_password(self):
        """Test behaviour with empty password."""
        resp = self.app.post(
            "/api/1.0/users/",
            data=json.dumps(
                dict(
                    name="UnitTest Post",
                    email="unittest@example.com",
                    username="UnitTester",
                    password="",
                )
            ),
            content_type="application/json"
        )

        response = json.loads(resp.get_data().decode())

        self.assertEquals(resp.status_code, 400)
        self.assertFalse(response["success"])

    def test_adding_user_with_too_short_password(self):
        """Test behaviour with too short password.
        See settings/config.py setting: MIN_PASSWORD_LENGTH"""
        resp = self.app.post(
            "/api/1.0/users/",
            data=json.dumps(
                dict(
                    name="UnitTest Post",
                    email="unittest@example.com",
                    username="UnitTester",
                    password="short",
                )
            ),
            content_type="application/json"
        )

        response = json.loads(resp.get_data().decode())

        self.assertEquals(resp.status_code, 400)
        self.assertFalse(response["success"])

    def test_updating_user(self):
        """Should update the given entry with the data in the JSON."""
        user_before = Users.query.filter_by(UserID=self.valid_users[0]).first()
        password_before = user_before.Password

        response = self.app.put(
            "/api/1.0/users/{}".format(self.valid_users[0]),
            data=json.dumps(
                dict(
                    name="UnitTest Update",
                    email="unittest-update@example.com",
                    username="UnitTesterUpdate",
                    password="unittesting-update",
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        user_after = Users.query.filter_by(UserID=self.valid_users[0]).first()
        password_after = user_after.Password

        get_user = self.app.get(
            "/api/1.0/users/{}".format(self.valid_users[0]),
            headers={
                'User': self.valid_users[0],
                'Authorization': self.access_token
            }
        )
        userdata = json.loads(get_user.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(200, get_user.status_code)
        self.assertEquals("UnitTest Update", userdata["users"][0]["name"])
        self.assertEquals("unittest-update@example.com", userdata["users"][0]["email"])
        self.assertEquals("UnitTesterUpdate", userdata["users"][0]["username"])
        # Password should obviously not be in the response, but it should be updated.
        self.assertFalse("password" in userdata["users"][0])
        self.assertNotEquals(password_before, password_after)
        self.assertNotEquals("unittesting-update", password_after)
        # The hashed updated password must validate against the real cleartext password
        self.assertTrue(check_password_hash(password_after, "unittesting-update"))

    def test_updating_user_with_too_short_password(self):
        """Should not update the user."""
        response = self.app.put(
            "/api/1.0/users/{}".format(self.valid_users[0]),
            data=json.dumps(
                dict(
                    name="UnitTest Update",
                    email="unittest-update@example.com",
                    username="UnitTesterUpdate",
                    password="short",
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        get_user = self.app.get(
            "/api/1.0/users/{}".format(self.valid_users[0]),
            headers={
                'User': self.valid_users[0],
                'Authorization': self.access_token
            }
        )
        userdata = json.loads(get_user.get_data().decode())

        self.assertEquals(400, response.status_code)
        self.assertEquals(200, get_user.status_code)
        self.assertEquals("UnitTest", userdata["users"][0]["name"])
        # Should be none, since we never saved one originally
        self.assertEquals(None, userdata["users"][0]["email"])
        self.assertEquals("unittester", userdata["users"][0]["username"])
        # Password should obviously not be in the response
        self.assertFalse("password" in userdata["users"][0])
