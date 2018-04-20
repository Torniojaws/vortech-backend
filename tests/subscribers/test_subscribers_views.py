import json
import unittest

from flask_caching import Cache

from app import app, db
from apps.users.models import Users, UsersAccessLevels, UsersAccessTokens, UsersAccessMapping
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestSubscribersViews(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Add 3 users and make User 2 a subscriber
        user1 = Users(
            Name="UnitTest1",
            Username="unittester1",
            Password="unittest1",
            Email="unittest1@email",
            Created=get_datetime(),
        )
        user2 = Users(
            Name="UnitTest2",
            Username="unittester2",
            Password="unittest2",
            Subscriber=True,
            Created=get_datetime(),
        )
        user3 = Users(
            Name="UnitTest3",
            Username="unittester3",
            Password="unittest3",
            Created=get_datetime(),
        )
        user4 = Users(
            Name="UnitTest4",
            Username="unittester4",
            Password="unittest4",
            Email="unittest4@email",
            Subscriber=True,
            Created=get_datetime(),
        )
        user5 = Users(
            Name="UnitTest5",
            Username="unittester5",
            Password="unittest5",
            Created=get_datetime(),
        )
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)
        db.session.add(user5)
        db.session.commit()

        # Add user level for registered users, if not already
        if not UsersAccessLevels.query.filter_by(LevelName="Registered").first():
            registered = UsersAccessLevels(
                UsersAccessLevelID=2,
                LevelName="Registered"
            )
            db.session.add(registered)
            db.session.commit()

        register_user1 = UsersAccessMapping(
            UserID=user1.UserID,
            UsersAccessLevelID=2
        )
        register_user2 = UsersAccessMapping(
            UserID=user2.UserID,
            UsersAccessLevelID=2
        )
        register_user4 = UsersAccessMapping(
            UserID=user4.UserID,
            UsersAccessLevelID=2
        )
        register_user5 = UsersAccessMapping(
            UserID=user5.UserID,
            UsersAccessLevelID=2
        )

        # Define level for admin
        if not UsersAccessLevels.query.filter_by(LevelName="Admin").first():
            access_level = UsersAccessLevels(
                UsersAccessLevelID=4,
                LevelName="Admin"
            )
            db.session.add(access_level)
            db.session.commit()

        # Make user3 an admin
        user3_admin = UsersAccessMapping(
            UserID=user3.UserID,
            UsersAccessLevelID=4
        )

        self.access_token1 = "unittest1-access-token"
        self.access_token2 = "unittest2-access-token"
        self.access_token3 = "unittest3-access-token"
        self.access_token4 = "unittest4-access-token"
        self.access_token5 = "unittest5-access-token"
        user1_token = UsersAccessTokens(
            UserID=user1.UserID,
            AccessToken=self.access_token1,
            ExpirationDate=get_datetime_one_hour_ahead()
        )
        user2_token = UsersAccessTokens(
            UserID=user2.UserID,
            AccessToken=self.access_token2,
            ExpirationDate=get_datetime_one_hour_ahead()
        )
        user3_token = UsersAccessTokens(
            UserID=user3.UserID,
            AccessToken=self.access_token3,
            ExpirationDate=get_datetime_one_hour_ahead()
        )
        user4_token = UsersAccessTokens(
            UserID=user4.UserID,
            AccessToken=self.access_token4,
            ExpirationDate=get_datetime_one_hour_ahead()
        )
        user5_token = UsersAccessTokens(
            UserID=user5.UserID,
            AccessToken=self.access_token5,
            ExpirationDate=get_datetime_one_hour_ahead()
        )

        db.session.add(register_user1)
        db.session.add(register_user2)
        db.session.add(register_user4)
        db.session.add(register_user5)
        db.session.add(user3_admin)
        db.session.add(user1_token)
        db.session.add(user2_token)
        db.session.add(user3_token)
        db.session.add(user4_token)
        db.session.add(user5_token)

        db.session.commit()

        self.non_sub_with_email_id = user1.UserID
        self.non_sub_without_email_id = user5.UserID
        self.subscriber_with_email_id = user4.UserID
        self.subscriber_without_email_id = user2.UserID
        self.admin_id = user3.UserID

        self.valid_tokens = [
            self.access_token1, self.access_token2, self.access_token3, self.access_token4,
            self.access_token5
        ]

    def tearDown(self):
        for user in Users.query.all():
            db.session.delete(user)
        db.session.commit()

        for level in UsersAccessLevels.query.all():
            db.session.delete(level)
        db.session.commit()

    def test_getting_all_subscribers(self):
        """Should get all valid subscribers, when requested by an authenticated admin."""
        response = self.app.get(
            "/api/1.0/subscribers/",
            headers={
                'User': self.admin_id,
                'Authorization': self.valid_tokens[2]
            }
        )
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertTrue("subscribers" in data)
        self.assertEquals(1, len(data["subscribers"]))
        self.assertEquals(self.subscriber_with_email_id, data["subscribers"][0]["id"])

    def test_getting_one_subscriber(self):
        """Should get the specific subscriber, when requested by a registered user that is a
        subscriber."""
        response = self.app.get(
            "/api/1.0/subscribers/{}".format(self.subscriber_with_email_id),
            headers={
                'User': self.subscriber_with_email_id,
                'Authorization': self.valid_tokens[3]
            }
        )
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertTrue("subscribers" in data)
        self.assertEquals(1, len(data["subscribers"]))
        self.assertEquals(self.subscriber_with_email_id, data["subscribers"][0]["id"])
        self.assertEquals("unittest4@email", data["subscribers"][0]["email"])
        self.assertTrue(data["subscribers"][0]["subscriber"])

    def test_getting_one_subscriber_who_has_no_email(self):
        """Should return a 400 Bad Request with an error message."""
        response = self.app.get(
            "/api/1.0/subscribers/{}".format(self.subscriber_without_email_id),
            headers={
                'User': self.subscriber_without_email_id,
                'Authorization': self.valid_tokens[1]
            }
        )
        data = json.loads(response.data.decode())

        self.assertEquals(400, response.status_code)
        self.assertTrue("success" in data)
        self.assertFalse(data["success"])
        self.assertEquals("A valid email is required to subscribe", data["message"])

    def test_adding_subscription(self):
        """Should subscribe the specified user to news."""
        response = self.app.post(
            "/api/1.0/subscribers/",
            data=json.dumps(
                dict(
                    subscribe=True
                )
            ),
            content_type="application/json",
            headers={
                'User': self.non_sub_with_email_id,
                'Authorization': self.valid_tokens[0]
            }
        )
        data = json.loads(response.data.decode())

        user = Users.query.filter_by(UserID=self.non_sub_with_email_id).first()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertEquals(True, user.Subscriber)
        # Just a sanity test
        self.assertEquals("UnitTest1", user.Name)
        self.assertEquals("unittest1@email", user.Email)

    def test_adding_subscription_when_user_has_no_email(self):
        """Should return a 400 Bad Request and a message."""
        response = self.app.post(
            "/api/1.0/subscribers/",
            data=json.dumps(
                dict(
                    subscribe=True
                )
            ),
            content_type="application/json",
            headers={
                'User': self.non_sub_without_email_id,
                'Authorization': self.valid_tokens[4]
            }
        )
        data = json.loads(response.data.decode())

        self.assertEquals(400, response.status_code)
        self.assertTrue("success" in data)
        self.assertFalse(data["success"])
        self.assertEquals("A valid email is required to subscribe.", data["message"])

    def test_adding_subscription_to_already_subscribed(self):
        """Should keep the subscription the specified user has."""
        user_before = Users.query.filter_by(UserID=self.subscriber_with_email_id).first()

        response = self.app.post(
            "/api/1.0/subscribers/",
            data=json.dumps(
                dict(
                    subscribe=True
                )
            ),
            content_type="application/json",
            headers={
                'User': self.subscriber_with_email_id,
                'Authorization': self.valid_tokens[3]
            }
        )
        data = json.loads(response.data.decode())

        user_after = Users.query.filter_by(UserID=self.subscriber_with_email_id).first()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertTrue(user_before.Subscriber)
        self.assertTrue(user_after.Subscriber)

    def test_adding_subscription_for_wrong_userid(self):
        """If eg. UserID=123 tries to modify the request to have ID=555, it should return 401."""
        response = self.app.post(
            "/api/1.0/subscribers/",
            data=json.dumps(
                dict(
                    subscribe=True
                )
            ),
            content_type="application/json",
            headers={
                'User': self.non_sub_without_email_id,
                'Authorization': self.valid_tokens[3]
            }
        )

        self.assertEquals(401, response.status_code)

    def test_adding_subscription_with_no_token(self):
        """Should return 401."""
        response = self.app.post(
            "/api/1.0/subscribers/",
            data=json.dumps(
                dict(
                    subscribe=True
                )
            ),
            content_type="application/json",
            headers={
                'User': self.non_sub_with_email_id
            }
        )

        self.assertEquals(401, response.status_code)

    def test_adding_subscription_with_invalid_payload(self):
        """Should return 400 Bad Request."""
        response = self.app.post(
            "/api/1.0/subscribers/",
            data=json.dumps(
                dict(
                    invalid="Data"
                )
            ),
            content_type="application/json",
            headers={
                'User': self.non_sub_with_email_id,
                'Authorization': self.valid_tokens[0]
            }
        )

        self.assertEquals(400, response.status_code)

    def test_unsubscribing(self):
        """Should unsubscribe the specified user."""
        response = self.app.delete(
            "/api/1.0/subscribers/",
            headers={
                'User': self.subscriber_with_email_id,
                'Authorization': self.valid_tokens[3]
            }
        )

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

    def test_unsubscribing_with_wrong_token(self):
        """Should return 401."""
        response = self.app.delete(
            "/api/1.0/subscribers/",
            headers={
                'User': self.subscriber_with_email_id,
                'Authorization': self.valid_tokens[1]  # Does not match the user's token
            }
        )

        user = Users.query.filter_by(UserID=self.subscriber_with_email_id).first()

        self.assertEquals(401, response.status_code)
        # The attempted user should remain a subscriber
        self.assertTrue(user.Subscriber)
