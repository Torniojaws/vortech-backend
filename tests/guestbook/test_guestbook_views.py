"""There are two ways to post to the guestbook:
1) Guest user that is not logged in. All posts will be using the Guest account with a freeform name
2) Logged in users will have a link to their profile and their username is reserved from Guests
"""

import json
import unittest

from app import app, db
from apps.guestbook.models import Guestbook
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestGuestbookViews(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        # The users must exist
        user1 = Users(
            UserID=1,
            Name="UnitTest Guest",
            Email="unittest-guest@email.com",
            Username="unittest-guest",
            Password="asdasd",
            Created=get_datetime(),
        )
        user2 = Users(
            UserID=3,
            Name="UnitTest User",
            Email="unittest-user@email.com",
            Username="unittest-user",
            Password="asdasd",
            Created=get_datetime(),
        )
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # Add three test posts
        post1 = Guestbook(
            UserID=1,
            Author="UnitTest Name 1",
            Message="UnitTest Message 1",
            Created="2017-01-01 00:00:00",
            AdminComment="UnitTest Admin Comment 1"
        )
        post2 = Guestbook(
            UserID=1,
            Author="UnitTest Me too",
            Message="UnitTest another guestbook post",
            Created="2017-02-02 00:05:00",
        )
        post3 = Guestbook(
            UserID=3,
            Author="UnitTest Name 3",
            Message="UnitTest Message 3",
            Created="2017-02-05 00:05:00",
            AdminComment="UnitTest Admin Comment 3"
        )
        db.session.add(post1)
        db.session.add(post2)
        db.session.add(post3)
        db.session.commit()
        self.valid_post = post1.GuestbookID
        # This is used in patch add test to add an admin comment
        self.admin_valid_post = post2.GuestbookID

        # We also need a valid admin user for the add release endpoint test.
        user = Users(
            Name="UnitTest Admin",
            Username="unittest-admin",
            Password="password"
        )
        db.session.add(user)
        db.session.commit()

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

        self.user_id = user.UserID

    def tearDown(self):
        for post in Guestbook.query.filter(Guestbook.Author.like("UnitTest%")).all():
            db.session.delete(post)
        db.session.commit()

        for user in Users.query.filter(Users.Name.like("UnitTest%")).all():
            db.session.delete(user)
        db.session.commit()

    def test_getting_all_guestbook_posts(self):
        """Should return all guestbook posts in reverse chronological order, ie. newest first."""
        response = self.app.get("/api/1.0/guestbook/")
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(data["guestbook"]))

        self.assertEqual("UnitTest Name 1", data["guestbook"][2]["name"])
        self.assertEqual("UnitTest Message 1", data["guestbook"][2]["message"])
        self.assertTrue(data["guestbook"][2]["isGuest"])
        self.assertNotEqual("", data["guestbook"][2]["createdAt"])
        self.assertEqual("UnitTest Admin Comment 1", data["guestbook"][2]["adminComment"])

        self.assertEqual("UnitTest Name 3", data["guestbook"][0]["name"])
        self.assertEqual("UnitTest Message 3", data["guestbook"][0]["message"])
        self.assertFalse(data["guestbook"][0]["isGuest"])
        self.assertNotEqual("", data["guestbook"][0]["createdAt"])
        self.assertEqual("UnitTest Admin Comment 3", data["guestbook"][0]["adminComment"])

    def test_getting_one_guestbook_post(self):
        """Should return a given guestbook post."""
        response = self.app.get("/api/1.0/guestbook/{}".format(self.valid_post))
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(data["guestbook"]))

        self.assertEqual("UnitTest Name 1", data["guestbook"][0]["name"])
        self.assertEqual("UnitTest Message 1", data["guestbook"][0]["message"])
        self.assertTrue(data["guestbook"][0]["isGuest"])
        self.assertNotEqual("", data["guestbook"][0]["createdAt"])
        self.assertEqual("UnitTest Admin Comment 1", data["guestbook"][0]["adminComment"])

    def test_adding_guestbook_post_as_logged_user(self):
        """Should add it normally."""
        response = self.app.post(
            "/api/1.0/guestbook/",
            data=json.dumps(
                dict(
                    userID=3,
                    name="UnitTest Post",
                    message="UnitTest message",
                )
            ),
            content_type="application/json"
        )
        data = response.data.decode()

        book = Guestbook.query.filter_by(Author="UnitTest Post").first_or_404()

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in data)

        self.assertEqual(3, book.UserID)
        self.assertEqual("UnitTest Post", book.Author)
        self.assertEqual("UnitTest message", book.Message)

    def test_adding_guestbook_post_as_guest_user(self):
        """Should add it normally."""
        response = self.app.post(
            "/api/1.0/guestbook/",
            data=json.dumps(
                dict(
                    userID=1,
                    name="UnitTest Guest Post",
                    message="UnitTest Guest message",
                )
            ),
            content_type="application/json"
        )
        data = response.data.decode()

        book = Guestbook.query.filter_by(Author="UnitTest Guest Post").first_or_404()

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in data)

        self.assertEqual(1, book.UserID)
        self.assertEqual("UnitTest Guest Post", book.Author)
        self.assertEqual("UnitTest Guest message", book.Message)

    def test_adding_guestbook_post_as_guest_user_with_name_that_is_already_registered(self):
        """Should not add the post, and should return a 400 Bad Request with error JSON."""
        response = self.app.post(
            "/api/1.0/guestbook/",
            data=json.dumps(
                dict(
                    userID=1,
                    name="UnitTest User",
                    message="UnitTest Guest message should not exist",
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        book = Guestbook.query.filter_by(
            Message="UnitTest Guest message should not exist"
        ).first()

        self.assertEqual(400, response.status_code)
        self.assertEqual(None, book)
        self.assertFalse(data["success"])
        self.assertEqual("Username already in use by a registered user", data["error"])

    def test_patching_guestbook_using_add(self):
        """Should modify a resource in the specified guestbook post."""
        response = self.app.patch(
            "/api/1.0/guestbook/{}".format(self.admin_valid_post),
            data=json.dumps(
                [
                    dict({
                        "op": "add",
                        "path": "/adminComment",
                        "value": "UnitTest patched admin comment"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        book = Guestbook.query.filter_by(GuestbookID=self.admin_valid_post).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", response.data.decode())

        self.assertEqual("UnitTest patched admin comment", book.AdminComment)

    def test_patching_guestbook_using_copy(self):
        """Should copy a resource in the specified guestbook post to another resource."""
        response = self.app.patch(
            "/api/1.0/guestbook/{}".format(self.valid_post),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/author",
                        "path": "/adminComment",
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        book = Guestbook.query.filter_by(GuestbookID=self.valid_post).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", response.data.decode())

        self.assertEqual("UnitTest Name 1", book.AdminComment)

    # TODO: Move, Remove and Test will be implemented later

    def test_patching_guestbook_using_replace(self):
        """Should replace the value of a resource in the specified guestbook post with value."""
        response = self.app.patch(
            "/api/1.0/guestbook/{}".format(self.valid_post),
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/message",
                        "value": "UnitTest replaced message"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        book = Guestbook.query.filter_by(GuestbookID=self.valid_post).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", response.data.decode())

        self.assertEqual("UnitTest replaced message", book.Message)

    def test_patching_with_exception(self):
        """Test a patch that results in 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/guestbook/{}".format(self.valid_post),
            data=json.dumps(
                [
                    dict({
                        "op": "test",
                        "path": "/doesnotexist",
                        "value": "I do not exist"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEqual(422, response.status_code)
        self.assertFalse("", response.data.decode())

    def test_deleting_guestbook_post(self):
        """Should delete the post."""
        response = self.app.delete(
            "/api/1.0/guestbook/{}".format(self.valid_post),
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        book = Guestbook.query.filter_by(GuestbookID=self.valid_post).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual(None, book)
