import unittest

from app import app, db
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime_one_hour_ahead
from apps.utils.auth import (
    invalid_token,
    user_is_admin,
    user_is_registered_or_more,
)


class TestAuthFunctions(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        user = Users(
            Name="UnitTest User",
            Username="unittest",
            Password="password"
        )
        mapped_user = Users(
            Name="UnitTest Mapped",
            Username="unittest-mapped",
            Password="password"
        )
        admin = Users(
            Name="UnitTest Admin",
            Username="unittest-admin",
            Password="password"
        )
        guest = Users(
            Name="UnitTest Guest",
            Username="unittest-guest",
            Password="password"
        )
        db.session.add(user)
        db.session.add(mapped_user)
        db.session.add(admin)
        db.session.add(guest)
        db.session.commit()
        self.user_id = user.UserID
        self.mapped_user_id = mapped_user.UserID
        self.admin_id = admin.UserID
        self.guest_id = guest.UserID

        # Map as guest user
        if not UsersAccessLevels.query.filter_by(LevelName="Guest").first():
            guest_user = UsersAccessLevels(
                UsersAccessLevelID=1,
                LevelName="Guest"
            )
            db.session.add(guest_user)
            db.session.commit()

        grant_guest = UsersAccessMapping(
            UserID=self.guest_id,
            UsersAccessLevelID=1
        )
        db.session.add(grant_guest)
        db.session.commit()

        # Map as registered user
        if not UsersAccessLevels.query.filter_by(LevelName="Registered").first():
            registered = UsersAccessLevels(
                UsersAccessLevelID=2,
                LevelName="Registered"
            )
            db.session.add(registered)
            db.session.commit()

        grant_registered = UsersAccessMapping(
            UserID=self.mapped_user_id,
            UsersAccessLevelID=2
        )
        db.session.add(grant_registered)
        db.session.commit()

        # Grant admin
        if not UsersAccessLevels.query.filter_by(LevelName="Admin").first():
            access_level = UsersAccessLevels(
                UsersAccessLevelID=4,
                LevelName="Admin"
            )
            db.session.add(access_level)
            db.session.commit()

        grant_admin = UsersAccessMapping(
            UserID=self.admin_id,
            UsersAccessLevelID=4
        )
        db.session.add(grant_admin)
        db.session.commit()

        # This is non-standard, but is fine for testing.
        self.access_token = "unittest-access-token"
        user_token = UsersAccessTokens(
            UserID=user.UserID,
            AccessToken=self.access_token,
            ExpirationDate="2015-01-01 00:00:00"  # NB: This is expired on purpose
        )
        db.session.add(user_token)
        db.session.commit()

    def tearDown(self):
        user = Users.query.filter_by(Name="UnitTest User").first()
        db.session.delete(user)
        db.session.commit()

    def test_invalid_token_when_user_has_no_token(self):
        """When the given user (real or fake) has no token, this should return True."""
        self.assertTrue(invalid_token("wrong_user_id", "fake_token"))

    def test_invalid_token_when_user_has_a_valid_token(self):
        """This happens when UserID is correct and that ID has an existing token, but the request
        contains an invalid token (does not match the valid one). Should return True."""
        self.assertTrue(invalid_token(self.user_id, "fake_token"))

    def test_invalid_token_when_valid_token_has_expired(self):
        """When an expired token is used, should return True."""
        self.assertTrue(invalid_token(self.user_id, self.access_token))

    def test_invalid_token_when_user_and_token_are_ok(self):
        """The normal case, should return False."""
        # Create a valid token
        valid_token = UsersAccessTokens(
            UserID=self.admin_id,
            AccessToken="test-token-valid",
            ExpirationDate=get_datetime_one_hour_ahead()
        )
        db.session.add(valid_token)
        db.session.commit()

        self.assertFalse(invalid_token(self.admin_id, "test-token-valid"))

    def test_user_is_admin_with_invalid_user(self):
        """Should return False."""
        self.assertFalse(user_is_admin("fake"))

    def test_user_is_admin_with_valid_user_but_no_mapping(self):
        """Should return False. Mappings are done on a per-case basis (granting admin is rare)"""
        self.assertFalse(user_is_admin(self.user_id))

    def test_user_is_admin_with_valid_non_admin_user_with_mapping(self):
        """Should return False."""
        self.assertFalse(user_is_admin(self.mapped_user_id))

    def test_user_is_admin_with_valid_admin_user(self):
        """Should return True."""
        self.assertTrue(user_is_admin(self.admin_id))

    def test_user_is_registered_with_invalid_user(self):
        """Should return False."""
        self.assertFalse(user_is_registered_or_more("fake"))

    def test_user_is_registered_with_valid_user_but_no_mapping(self):
        """Should return False. Mappings are done on a per-case basis (granting admin is rare)"""
        self.assertFalse(user_is_registered_or_more(self.user_id))

    def test_user_is_registered_with_valid_registered_user(self):
        """Should return True."""
        self.assertTrue(user_is_registered_or_more(self.mapped_user_id))

    def test_user_is_registered_with_guest_user(self):
        """Should return False. Guest users normally only post in Guestbook(!), where any non-zero
        mapping is considered as guest level."""
        self.assertFalse(user_is_registered_or_more(self.guest_id))

    def test_admin_only_with_invalid_user_token(self):
        """Test the admin-only decorator in Releases endpoint with invalid auth."""
        response = self.app.post(
            "/api/1.0/releases/",
            data=None,  # For this test, we don't need a real payload
            headers={
                'User': "invalid",
                'Authorization': "wrong"
            }
        )
        self.assertEquals(401, response.status_code)

    def test_admin_only_with_valid_user_and_invalid_token(self):
        """Test the admin-only decorator in Releases endpoint with valid user but invalid token."""
        response = self.app.post(
            "/api/1.0/releases/",
            data=None,  # For this test, we don't need a real payload
            headers={
                'User': self.admin_id,
                'Authorization': "wrong"
            }
        )
        self.assertEquals(401, response.status_code)

    def test_admin_only_with_missing_user_and_invalid_token(self):
        """Test the admin-only decorator in Releases endpoint with valid user but invalid token."""
        response = self.app.post(
            "/api/1.0/releases/",
            data=None,  # For this test, we don't need a real payload
            headers={
                'Authorization': "wrong"
            }
        )
        self.assertEquals(401, response.status_code)

    def test_registered_only_with_invalid_user_token(self):
        """Test the registered users-only decorator in GET /users/:id endpoint with invalid auth."""
        response = self.app.get(
            "/api/1.0/users/{}".format(self.user_id),
            headers={
                'User': "invalid",
                'Authorization': "wrong"
            }
        )
        self.assertEquals(401, response.status_code)

    def test_registered_only_with_valid_user_and_invalid_token(self):
        """Test the registered users-only decorator in GET /users/:id endpoint with valid user but
        invalid auth."""
        response = self.app.get(
            "/api/1.0/users/{}".format(self.user_id),
            headers={
                'User': self.admin_id,
                'Authorization': "wrong"
            }
        )
        self.assertEquals(401, response.status_code)

    def test_registered_only_with_missing_user_and_invalid_token(self):
        """Test the registered users-only decorator in GET /users/:id endpoint with missing user
        and invalid auth."""
        response = self.app.get(
            "/api/1.0/users/{}".format(self.user_id),
            headers={
                'Authorization': "wrong"
            }
        )
        self.assertEquals(401, response.status_code)
