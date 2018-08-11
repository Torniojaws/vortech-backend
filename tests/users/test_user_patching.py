import json
import unittest

from app import db

from apps.users.models import Users, UsersAccessLevels, UsersAccessMapping
from apps.users.patches import get_value, patch_item
from apps.utils.time import get_datetime

from werkzeug.security import check_password_hash, generate_password_hash


class TestUsersPatches(unittest.TestCase):
    def setUp(self):
        self
        self.valid_users = []
        self.user_created = []
        # Create 3 users
        for i in range(1, 4):
            # This is for the "test" operation
            created = get_datetime()
            self.user_created.append(created)
            user = Users(
                Name="UnitTester {}".format(i),
                Email="unittest{}@email.com".format(i),
                Username="unittest{}".format(i),
                Password=generate_password_hash("UnitTesting{}".format(i)),
                Subscriber=False,
                Created=created,
            )

            # For testing the "test" op
            if i == 3:
                user.Updated = created
                self.user_updated = created

            db.session.add(user)
            db.session.commit()
            self.valid_users.append(user.UserID)

        # Create level 3
        level = UsersAccessLevels(
            UsersAccessLevelID=3,
            LevelName="Registered"
        )
        db.session.add(level)
        db.session.commit()

        # Make user[1] and user[2] level 3 for testing purposes
        mapping1 = UsersAccessMapping(UserID=self.valid_users[1], UsersAccessLevelID=3)
        mapping2 = UsersAccessMapping(UserID=self.valid_users[2], UsersAccessLevelID=3)
        db.session.add(mapping1)
        db.session.add(mapping2)
        db.session.commit()

    def tearDown(self):
        for user in Users.query.all():
            db.session.delete(user)
        db.session.commit()
        for level in UsersAccessLevels.query.all():
            db.session.delete(level)
        db.session.commit()

    def test_simple_patches(self):
        """Test some simple cases."""
        payload = json.dumps([
            {"op": "add", "path": "/name", "value": "New name"},
            {"op": "copy", "from": "/email", "path": "/username"},
            {"op": "replace", "path": "/subscriber", "value": True}
        ])
        result = patch_item(self.valid_users[0], payload)
        user = Users.query.filter_by(UserID=self.valid_users[0]).first_or_404()
        self.assertEquals("New name", result["name"])
        self.assertEquals("unittest1@email.com", result["username"])
        self.assertEquals(True, result["subscriber"])
        self.assertEquals("New name", user.Name)
        self.assertEquals("unittest1@email.com", user.Username)
        self.assertEquals(True, user.Subscriber)
        self.assertNotEquals(None, user.Updated)  # Should update automatically

    def test_less_common_patches(self):
        """These are probably not used a lot."""
        payload = json.dumps([
            {"op": "test", "path": "/level", "value": 3},
            {"op": "move", "from": "/email", "path": "/username"},
            {"op": "remove", "path": "/created"}
        ])
        result = patch_item(self.valid_users[1], payload)
        user = Users.query.filter_by(UserID=self.valid_users[1]).first_or_404()
        self.assertEquals("unittest2@email.com", result["username"])
        self.assertEquals(None, result["created"])
        self.assertEquals("unittest2@email.com", user.Username)
        self.assertEquals(None, user.Created)
        self.assertNotEquals(None, user.Updated)  # Should update automatically

    def test_each_add(self):
        payload = json.dumps([
            {"op": "add", "path": "/email", "value": "New email"},
            {"op": "add", "path": "/username", "value": "New username"},
            {"op": "add", "path": "/password", "value": "New password"},
            {"op": "add", "path": "/level", "value": 2},
            {"op": "add", "path": "/subscriber", "value": True},
        ])
        result = patch_item(self.valid_users[2], payload)
        user = Users.query.filter_by(UserID=self.valid_users[2]).first_or_404()
        self.assertEquals("New email", result["email"])
        self.assertEquals("New username", result["username"])
        self.assertEquals("The password has been updated", result["password"])
        self.assertEquals("User level is not allowed to be changed with PATCH", result["level"])
        self.assertEquals(True, result["subscriber"])
        self.assertEquals("New email", user.Email)
        self.assertEquals("New username", user.Username)
        self.assertEquals(True, check_password_hash(user.Password, "New password"))
        self.assertEquals(True, user.Subscriber)

    def test_move(self):
        payload = json.dumps([{"op": "move", "from": "/created", "path": "/updated"}])
        result = patch_item(self.valid_users[0], payload)
        user = Users.query.filter_by(UserID=self.valid_users[0]).first_or_404()
        self.assertEquals(None, user.Created)
        self.assertNotEquals(None, result["updated"])

    def test_remove(self):
        """NB: We always populate User.Updated after a successful patch, so it will not be None
        in the database."""
        payload = json.dumps([
            {"op": "remove", "path": "/email"},
            {"op": "remove", "path": "/created"},
            {"op": "remove", "path": "/updated"},
        ])
        result = patch_item(self.valid_users[1], payload)
        user = Users.query.filter_by(UserID=self.valid_users[1]).first_or_404()
        self.assertEquals(None, user.Email)
        self.assertEquals(None, user.Created)
        self.assertNotEquals(None, user.Updated)  # Will be populated after success
        self.assertEquals(None, result["email"])
        self.assertEquals(None, result["created"])
        self.assertEquals(None, result["updated"])  # But here it is explicitly None after success

    def test_tests(self):
        """Verify the "test" operations for each valid path. The "test" operation does not return
        anything to the endpoint itself, so we do an "add" as the last step. If any test fails
        before that, an error response is returned instead."""
        payload = json.dumps([
            {"op": "test", "path": "/name", "value": "UnitTester 2"},
            {"op": "test", "path": "/email", "value": "unittest2@email.com"},
            {"op": "test", "path": "/username", "value": "unittest2"},
            {"op": "test", "path": "/password", "value": "UnitTesting2"},
            {"op": "test", "path": "/level", "value": 3},
            {"op": "test", "path": "/subscriber", "value": False},
            {"op": "test", "path": "/created", "value": self.user_created[1]},
            {"op": "test", "path": "/updated", "value": None},
            {"op": "add", "path": "/name", "value": "Passed the tests"}
        ])
        result = patch_item(self.valid_users[1], payload)  # NB: Only user[1] has a level
        user = Users.query.filter_by(UserID=self.valid_users[1]).first_or_404()
        self.assertEquals("Passed the tests", result["name"])
        self.assertEquals("Passed the tests", user.Name)

    def test_special_cases(self):
        """For coverage."""
        payload = json.dumps([
            {"op": "test", "path": "/updated", "value": self.user_updated},
            {"op": "replace", "path": "/name", "value": "Passed the tests"},
            {"op": "replace", "path": "/email", "value": "Passed the tests"},
            {"op": "replace", "path": "/password", "value": "Passed the tests"},
            {"op": "replace", "path": "/level", "value": "Passed the tests"},
            {"op": "replace", "path": "/created", "value": "Passed the tests"},
        ])
        result = patch_item(self.valid_users[2], payload)  # users[2] has an Updated value
        user = Users.query.filter_by(UserID=self.valid_users[2]).first_or_404()
        self.assertEquals("Passed the tests", result["name"])
        self.assertEquals("Passed the tests", result["email"])
        self.assertTrue(check_password_hash(user.Password, "Passed the tests"))
        self.assertEquals("Changing user level is not allowed", result["level"])
        self.assertEquals("Changing the creation date is not allowed", result["created"])
        self.assertEquals("Passed the tests", user.Name)
        self.assertEquals("Passed the tests", user.Email)

    def test_get_values(self):
        user = Users.query.filter_by(UserID=self.valid_users[2]).first_or_404()
        self.assertEquals("UnitTester 3", get_value(user, "/name"))
        self.assertEquals("unittest3@email.com", get_value(user, "/email"))
        self.assertEquals("unittest3", get_value(user, "/username"))
        self.assertEquals(3, get_value(user, "/level"))
        self.assertEquals(False, get_value(user, "/subscriber"))
        self.assertEquals(self.user_created[2], get_value(user, "/created"))
        self.assertEquals(self.user_updated, get_value(user, "/updated"))
        self.assertEquals("", get_value(user, "/doesnotexist"))
