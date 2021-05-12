import json
import unittest

from app import db

from apps.users.patches import patch_item
from apps.users.models import Users
from apps.utils.time import get_datetime


class TestUsersPatchesFailures(unittest.TestCase):
    def setUp(self):
        self.valid_users = []
        # Create 3 users
        for i in range(1, 4):
            user = Users(
                Name="UnitTester {}".format(i),
                Email="unittest{}@email.com".format(i),
                Username="unittest{}".format(i),
                Password="UnitTesting{}".format(i),
                Subscriber=False,
                Created=get_datetime(),
            )
            db.session.add(user)
            db.session.commit()
            self.valid_users.append(user.UserID)

    def tearDown(self):
        for user in Users.query.all():
            db.session.delete(user)
        db.session.commit()

    def test_a_failing_test_operation(self):
        payload = json.dumps([{"op": "test", "path": "/username", "value": "invalid"}])
        result = patch_item(self.valid_users[0], payload)
        self.assertFalse(result["success"])
        self.assertEqual("Test comparison did not match", result["message"])

    def test_an_invalid_operation(self):
        payload = json.dumps([{"op": "doesnotexist", "path": "/username", "value": "invalid"}])
        result = patch_item(self.valid_users[1], payload)
        self.assertFalse(result["success"])
        self.assertEqual("The patch contained invalid operations", result["message"])

    def test_invalid_move(self):
        payload = json.dumps([{"op": "move", "from": "/username", "path": "/email"}])
        result = patch_item(self.valid_users[2], payload)
        self.assertFalse(result["success"])
        self.assertEqual("The patch contained invalid operations", result["message"])

    def test_invalid_remove(self):
        payload = json.dumps([{"op": "remove", "path": "/username"}])
        result = patch_item(self.valid_users[0], payload)
        self.assertFalse(result["success"])
        self.assertEqual("The patch contained invalid operations", result["message"])

    def test_invalid_path_in_test_op(self):
        payload = json.dumps([{"op": "test", "path": "/doesnotexist", "value": "foo"}])
        result = patch_item(self.valid_users[1], payload)
        self.assertFalse(result["success"])
        self.assertEqual("Test comparison did not match", result["message"])

    def test_adding_too_short_password(self):
        payload = json.dumps([{"op": "add", "path": "/password", "value": "a"}])
        result = patch_item(self.valid_users[2], payload)
        self.assertFalse(result["success"])
        self.assertEqual("The patch contained invalid operations", result["message"])

    def test_replacing_with_too_short_password(self):
        payload = json.dumps([{"op": "replace", "path": "/password", "value": "a"}])
        result = patch_item(self.valid_users[0], payload)
        self.assertFalse(result["success"])
        self.assertEqual("The patch contained invalid operations", result["message"])

    def test_replacing_nonexisting_path(self):
        payload = json.dumps([{"op": "replace", "path": "/doesnotexist", "value": "a"}])
        result = patch_item(self.valid_users[1], payload)
        self.assertFalse(result["success"])
        self.assertEqual("The patch contained invalid operations", result["message"])
