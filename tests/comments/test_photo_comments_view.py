import json
import unittest

from flask_caching import Cache
from sqlalchemy import asc

from app import app, db
from apps.comments.models import CommentsPhotos
from apps.photos.models import Photos
from apps.users.models import Users, UsersAccessLevels, UsersAccessMapping, UsersAccessTokens
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestCommentsPhotosView(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "RedisCache"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Add three photos
        photo1 = Photos(
            Image="unittest1.jpg",
            Caption="UnitTest1",
            TakenBy="UnitTester",
            Country="UnitTest",
            CountryCode="UT",
            City="UnitTest",
            Created=get_datetime(),
        )
        photo2 = Photos(
            Image="unittest2.jpg",
            Caption="UnitTest2",
            TakenBy="UnitTester",
            Country="UnitTest",
            CountryCode="UT",
            City="UnitTest",
            Created=get_datetime(),
        )
        photo3 = Photos(
            Image="unittest3.jpg",
            Caption="UnitTest3",
            TakenBy="UnitTester",
            Country="UnitTest",
            CountryCode="UT",
            City="UnitTest",
            Created=get_datetime(),
        )
        db.session.add(photo1)
        db.session.add(photo2)
        db.session.add(photo3)
        db.session.commit()

        # Add two registered users
        user1 = Users(
            Name="UnitTest1",
            Username="unittester1",
            Password="unittest1",
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

        self.access_token1 = "unittest1-access-token"
        self.access_token2 = "unittest2-access-token"
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

        db.session.add(register_user1)
        db.session.add(register_user2)
        db.session.add(user1_token)
        db.session.add(user2_token)
        db.session.commit()

        self.valid_users = [user1.UserID, user2.UserID]
        self.valid_tokens = [self.access_token1, self.access_token2]

        self.photo_ids = [photo1.PhotoID, photo2.PhotoID, photo3.PhotoID]

        # Add some comments for each photo
        p1_comment1 = CommentsPhotos(
            PhotoID=self.photo_ids[0],
            Comment="P1C1 Comment",
            UserID=self.valid_users[0],
            Created=get_datetime()
        )
        p1_comment2 = CommentsPhotos(
            PhotoID=self.photo_ids[0],
            Comment="P1C2 Comment",
            UserID=self.valid_users[1],
            Created=get_datetime()
        )
        p2_comment1 = CommentsPhotos(
            PhotoID=self.photo_ids[1],
            Comment="P2C1 Comment",
            UserID=self.valid_users[0],
            Created=get_datetime()
        )
        p3_comment1 = CommentsPhotos(
            PhotoID=self.photo_ids[2],
            Comment="P3C1 Comment",
            UserID=self.valid_users[0],
            Created=get_datetime()
        )
        db.session.add(p1_comment1)
        db.session.add(p1_comment2)
        db.session.add(p2_comment1)
        db.session.add(p3_comment1)
        db.session.commit()

        self.valid_comment_ids = [
            p1_comment1.CommentID,
            p1_comment2.CommentID,
            p2_comment1.CommentID,
            p3_comment1.CommentID,
        ]
        self.valid_comment_ids_userid = [
            p1_comment1.UserID,
            p1_comment2.UserID,
            p2_comment1.UserID,
            p3_comment1.UserID,
        ]

    def tearDown(self):
        # Deleting a photo will also delete the comments for it
        for photo in Photos.query.all():
            db.session.delete(photo)
        db.session.commit()

        for user in Users.query.filter(Users.Username.like("unittest%")).all():
            db.session.delete(user)
        db.session.commit()

        access = UsersAccessLevels.query.filter_by(LevelName="Registered").first()
        db.session.delete(access)
        db.session.commit()

    def test_getting_all_comments(self):
        """Should return the current votes for all photos."""
        response = self.app.get("/api/1.0/comments/photos/")
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertEqual(4, len(data["comments"]))
        self.assertTrue(data["comments"][0]["photoID"] in self.photo_ids)
        self.assertTrue(data["comments"][1]["photoID"] in self.photo_ids)
        self.assertTrue(data["comments"][2]["photoID"] in self.photo_ids)
        self.assertTrue(data["comments"][3]["photoID"] in self.photo_ids)

    def test_getting_comments_for_one_photo(self):
        """Should return the comments for the specified photo."""
        response = self.app.get("/api/1.0/comments/photos/{}".format(self.photo_ids[0]))
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertEqual(2, len(data["comments"]))
        self.assertEqual(self.photo_ids[0], data["comments"][0]["photoID"])
        self.assertEqual("UnitTest1", data["comments"][0]["name"])
        self.assertEqual("P1C1 Comment", data["comments"][0]["comment"])
        self.assertEqual("UnitTest2", data["comments"][1]["name"])
        self.assertEqual("P1C2 Comment", data["comments"][1]["comment"])

    def test_adding_a_comment_as_registered_user(self):
        """Should add a new comment with the userID."""
        response = self.app.post(
            "/api/1.0/comments/photos/",
            data=json.dumps(
                dict(
                    photoID=self.photo_ids[2],
                    comment="P3 UnitTest Brand New"
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[1],
                "Authorization": self.valid_tokens[1]
            }
        )

        comments = CommentsPhotos.query.filter_by(PhotoID=self.photo_ids[2]).order_by(
            asc(CommentsPhotos.CommentID)
        ).all()

        self.assertEqual(201, response.status_code)
        self.assertEqual(2, len(comments))
        self.assertEqual("P3C1 Comment", comments[0].Comment)
        self.assertEqual("P3 UnitTest Brand New", comments[1].Comment)
        self.assertEqual(self.valid_users[1], comments[1].UserID)

    def test_adding_a_comment_as_registered_user_with_invalid_token(self):
        """Should throw a 401, since it is an invalid case."""
        response = self.app.post(
            "/api/1.0/comments/photos/",
            data=json.dumps(
                dict(
                    photoID=self.photo_ids[2],
                    comment="P3 UnitTest Comment Same",
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[0],
                "Authorization": "not valid"
            }
        )

        comments = CommentsPhotos.query.filter_by(PhotoID=self.photo_ids[1]).order_by(
            asc(CommentsPhotos.CommentID)
        ).all()

        self.assertEqual(401, response.status_code)
        self.assertEqual(1, len(comments))
        self.assertEqual("P2C1 Comment", comments[0].Comment)

    def test_adding_another_comment_as_registered_user_for_same_photo(self):
        """Should add a second comment normally."""
        response = self.app.post(
            "/api/1.0/comments/photos/",
            data=json.dumps(
                dict(
                    photoID=self.photo_ids[2],
                    comment="P3 UnitTest Comment Same",
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[0],
                "Authorization": self.valid_tokens[0]
            }
        )

        comments = CommentsPhotos.query.filter_by(PhotoID=self.photo_ids[2]).order_by(
            asc(CommentsPhotos.CommentID)
        ).all()

        self.assertEqual(201, response.status_code)
        self.assertEqual(2, len(comments))
        self.assertEqual("P3C1 Comment", comments[0].Comment)
        self.assertEqual("P3 UnitTest Comment Same", comments[1].Comment)

    def test_editing_a_comment(self):
        """Should modify an existing comment."""
        response = self.app.put(
            "api/1.0/comments/photos/{}".format(self.photo_ids[0]),
            data=json.dumps(
                dict(
                    commentID=self.valid_comment_ids[0],
                    comment="UnitTest Edited"
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[0],
                "Authorization": self.valid_tokens[0]
            }
        )

        comments = CommentsPhotos.query.filter_by(PhotoID=self.photo_ids[0]).order_by(
            asc(CommentsPhotos.CommentID)
        ).all()

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(comments))
        self.assertEqual("UnitTest Edited", comments[0].Comment)
        self.assertEqual("P1C2 Comment", comments[1].Comment)

    def test_editing_a_comment_without_comment_id(self):
        """Should return 400 Bad Request."""
        response = self.app.put(
            "api/1.0/comments/photos/{}".format(self.photo_ids[0]),
            data=json.dumps(
                dict(
                    comment="UnitTest Edited"
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[0],
                "Authorization": self.valid_tokens[0]
            }
        )
        self.assertEqual(400, response.status_code)

    def test_editing_a_comment_without_comment(self):
        """Should return 400 Bad Request."""
        response = self.app.put(
            "api/1.0/comments/photos/{}".format(self.photo_ids[0]),
            data=json.dumps(
                dict(
                    commentID=self.valid_comment_ids[0]
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[0],
                "Authorization": self.valid_tokens[0]
            }
        )
        self.assertEqual(400, response.status_code)

    def test_editing_a_comment_with_wrong_userid(self):
        """Should return 401 Unauthorized. You can only edit your own comments."""
        response = self.app.put(
            "api/1.0/comments/photos/{}".format(self.photo_ids[1]),
            data=json.dumps(
                dict(
                    commentID=self.valid_comment_ids[1],
                    comment="UnitTest Edited"
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_comment_ids_userid[0],
                "Authorization": self.valid_tokens[0]
            }
        )
        self.assertEqual(401, response.status_code)

    def test_deleting_a_comment(self):
        """Should delete the comment."""
        response = self.app.delete(
            "api/1.0/comments/photos/{}".format(self.photo_ids[0]),
            data=json.dumps(
                dict(
                    commentID=self.valid_comment_ids[0]
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_comment_ids_userid[0],
                "Authorization": self.valid_tokens[0]
            }
        )

        comments = CommentsPhotos.query.filter_by(PhotoID=self.photo_ids[0]).all()

        self.assertEqual(204, response.status_code)
        self.assertEqual(1, len(comments))
        self.assertEqual("P1C2 Comment", comments[0].Comment)

    def test_deleting_a_comment_with_invalid_comment_id(self):
        """Should return 400 Bad Request."""
        response = self.app.delete(
            "api/1.0/comments/photos/{}".format(self.photo_ids[0]),
            data=json.dumps(
                dict(
                    commentID=None
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_comment_ids_userid[0],
                "Authorization": self.valid_tokens[0]
            }
        )
        self.assertEqual(400, response.status_code)

    def test_deleting_a_comment_with_invalid_user_id(self):
        """Should return 401 Unauthorized."""
        response = self.app.delete(
            "api/1.0/comments/photos/{}".format(self.photo_ids[0]),
            data=json.dumps(
                dict(
                    commentID=self.valid_comment_ids[0]
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_comment_ids_userid[1],
                "Authorization": self.valid_tokens[1]
            }
        )
        self.assertEqual(401, response.status_code)
