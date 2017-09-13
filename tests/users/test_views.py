import unittest

from app import app, db
from apps.users.models import Users
from apps.utils.time import get_datetime


class TestUsersView(unittest.TestCase):
    def setUp(self):
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

        self.valid_users = [user1.UserID, user2.UserID]

    def tearDown(self):
        delete_user = Users.query.filter(Users.Name.like("UnitTest%")).all()
        for user in delete_user:
            db.session.delete(user)

        db.session.commit()

    def test_getting_one_user(self):
        """Should return just one user's details"""
        pass
