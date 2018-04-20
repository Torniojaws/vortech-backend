import json
import unittest

from flask_caching import Cache
from sqlalchemy import asc

from app import app, db
from apps.comments.models import CommentsVideos
from apps.videos.models import Videos
from apps.users.models import Users, UsersAccessLevels, UsersAccessMapping, UsersAccessTokens
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestCommentsVideosView(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Add three videos
        video1 = Videos(
            Title="UnitTest1",
            URL="https://unittest1.com",
            Created=get_datetime(),
        )
        video2 = Videos(
            Title="UnitTest2",
            URL="https://unittest2.com",
            Created=get_datetime(),
        )
        video3 = Videos(
            Title="UnitTest3",
            URL="https://unittest3.com",
            Created=get_datetime(),
        )
        db.session.add(video1)
        db.session.add(video2)
        db.session.add(video3)
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

        self.video_ids = [video1.VideoID, video2.VideoID, video3.VideoID]

        # Add some comments for each video
        v1_comment1 = CommentsVideos(
            VideoID=self.video_ids[0],
            Comment="V1C1 Comment",
            UserID=self.valid_users[0],
            Created=get_datetime()
        )
        v1_comment2 = CommentsVideos(
            VideoID=self.video_ids[0],
            Comment="V1C2 Comment",
            UserID=self.valid_users[1],
            Created=get_datetime()
        )
        v2_comment1 = CommentsVideos(
            VideoID=self.video_ids[1],
            Comment="V2C1 Comment",
            UserID=self.valid_users[0],
            Created=get_datetime()
        )
        v3_comment1 = CommentsVideos(
            VideoID=self.video_ids[2],
            Comment="V3C1 Comment",
            UserID=self.valid_users[0],
            Created=get_datetime()
        )
        db.session.add(v1_comment1)
        db.session.add(v1_comment2)
        db.session.add(v2_comment1)
        db.session.add(v3_comment1)
        db.session.commit()

        self.valid_comment_ids = [
            v1_comment1.CommentID,
            v1_comment2.CommentID,
            v2_comment1.CommentID,
            v3_comment1.CommentID,
        ]
        self.valid_comment_ids_userid = [
            v1_comment1.UserID,
            v1_comment2.UserID,
            v2_comment1.UserID,
            v3_comment1.UserID,
        ]

    def tearDown(self):
        # Deleting a video will also delete the comments for it
        for video in Videos.query.all():
            db.session.delete(video)
        db.session.commit()

        for user in Users.query.filter(Users.Username.like("unittest%")).all():
            db.session.delete(user)
        db.session.commit()

        access = UsersAccessLevels.query.filter_by(LevelName="Registered").first()
        db.session.delete(access)
        db.session.commit()

    def test_getting_all_comments(self):
        """Should return the current votes for all videos."""
        response = self.app.get("/api/1.0/comments/videos/")
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(4, len(data["comments"]))
        self.assertTrue(data["comments"][0]["videoID"] in self.video_ids)
        self.assertTrue(data["comments"][1]["videoID"] in self.video_ids)
        self.assertTrue(data["comments"][2]["videoID"] in self.video_ids)
        self.assertTrue(data["comments"][3]["videoID"] in self.video_ids)

    def test_getting_comments_for_one_video(self):
        """Should return the comments for the specified video."""
        response = self.app.get("/api/1.0/comments/videos/{}".format(self.video_ids[0]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(2, len(data["comments"]))
        self.assertEquals(self.video_ids[0], data["comments"][0]["videoID"])
        self.assertEquals("UnitTest1", data["comments"][0]["name"])
        self.assertEquals("V1C1 Comment", data["comments"][0]["comment"])
        self.assertEquals("UnitTest2", data["comments"][1]["name"])
        self.assertEquals("V1C2 Comment", data["comments"][1]["comment"])

    def test_adding_a_comment_as_registered_user(self):
        """Should add a new comment with the userID."""
        response = self.app.post(
            "/api/1.0/comments/videos/",
            data=json.dumps(
                dict(
                    videoID=self.video_ids[2],
                    comment="V3 UnitTest Brand New"
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[1],
                "Authorization": self.valid_tokens[1]
            }
        )

        comments = CommentsVideos.query.filter_by(VideoID=self.video_ids[2]).order_by(
            asc(CommentsVideos.CommentID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertEquals(2, len(comments))
        self.assertEquals("V3C1 Comment", comments[0].Comment)
        self.assertEquals("V3 UnitTest Brand New", comments[1].Comment)
        self.assertEquals(self.valid_users[1], comments[1].UserID)

    def test_adding_a_comment_as_registered_user_with_invalid_token(self):
        """Should throw a 401, since it is an invalid case."""
        response = self.app.post(
            "/api/1.0/comments/videos/",
            data=json.dumps(
                dict(
                    videoID=self.video_ids[2],
                    comment="V3 UnitTest Comment Same",
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[0],
                "Authorization": "not valid"
            }
        )

        comments = CommentsVideos.query.filter_by(VideoID=self.video_ids[1]).order_by(
            asc(CommentsVideos.CommentID)
        ).all()

        self.assertEquals(401, response.status_code)
        self.assertEquals(1, len(comments))
        self.assertEquals("V2C1 Comment", comments[0].Comment)

    def test_adding_another_comment_as_registered_user_for_same_video(self):
        """Should add a second comment normally."""
        response = self.app.post(
            "/api/1.0/comments/videos/",
            data=json.dumps(
                dict(
                    videoID=self.video_ids[2],
                    comment="V3 UnitTest Comment Same",
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_users[0],
                "Authorization": self.valid_tokens[0]
            }
        )

        comments = CommentsVideos.query.filter_by(VideoID=self.video_ids[2]).order_by(
            asc(CommentsVideos.CommentID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertEquals(2, len(comments))
        self.assertEquals("V3C1 Comment", comments[0].Comment)
        self.assertEquals("V3 UnitTest Comment Same", comments[1].Comment)

    def test_editing_a_comment(self):
        """Should modify an existing comment."""
        response = self.app.put(
            "api/1.0/comments/videos/{}".format(self.video_ids[0]),
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

        comments = CommentsVideos.query.filter_by(VideoID=self.video_ids[0]).order_by(
            asc(CommentsVideos.CommentID)
        ).all()

        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len(comments))
        self.assertEquals("UnitTest Edited", comments[0].Comment)
        self.assertEquals("V1C2 Comment", comments[1].Comment)

    def test_editing_a_comment_without_comment_id(self):
        """Should return 400 Bad Request."""
        response = self.app.put(
            "api/1.0/comments/videos/{}".format(self.video_ids[0]),
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
        self.assertEquals(400, response.status_code)

    def test_editing_a_comment_without_comment(self):
        """Should return 400 Bad Request."""
        response = self.app.put(
            "api/1.0/comments/videos/{}".format(self.video_ids[0]),
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
        self.assertEquals(400, response.status_code)

    def test_editing_a_comment_with_wrong_userid(self):
        """Should return 401 Unauthorized. You can only edit your own comments."""
        response = self.app.put(
            "api/1.0/comments/videos/{}".format(self.video_ids[1]),
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
        self.assertEquals(401, response.status_code)

    def test_deleting_a_comment(self):
        """Should delete the comment."""
        response = self.app.delete(
            "api/1.0/comments/videos/{}".format(self.video_ids[0]),
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

        comments = CommentsVideos.query.filter_by(VideoID=self.video_ids[0]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals(1, len(comments))
        self.assertEquals("V1C2 Comment", comments[0].Comment)

    def test_deleting_a_comment_with_invalid_comment_id(self):
        """Should return 400 Bad Request."""
        response = self.app.delete(
            "api/1.0/comments/videos/{}".format(self.video_ids[0]),
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
        self.assertEquals(400, response.status_code)

    def test_deleting_a_comment_with_invalid_user_id(self):
        """Should return 401 Unauthorized."""
        response = self.app.delete(
            "api/1.0/comments/videos/{}".format(self.video_ids[0]),
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
        self.assertEquals(401, response.status_code)
