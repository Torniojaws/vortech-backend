import json
import unittest

from flask_caching import Cache

from app import app, db
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime_one_hour_ahead
from apps.videos.models import Videos, VideoCategories, VideosCategoriesMapping


class TestVideosViews(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "RedisCache"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Add 3 test video entries, 2 categories and the mapping
        video1 = Videos(
            Title="UnitTest Video 1",
            URL="http://www.example.com/video1",
            Created="2017-05-06 10:20:30"
        )
        video2 = Videos(
            Title="UnitTest Video 2",
            URL="http://www.example.com/video2",
            Created="2017-06-07 11:23:30"
        )
        video3 = Videos(
            Title="UnitTest Video 3",
            URL="http://www.example.com/video3",
            Created="2017-07-08 12:24:35"
        )
        db.session.add(video1)
        db.session.add(video2)
        db.session.add(video3)
        db.session.commit()
        self.valid_video_ids = [
            video1.VideoID,
            video2.VideoID,
            video3.VideoID,
        ]

        video_cat1 = VideoCategories(
            Category="UnitTest Cat"
        )
        video_cat2 = VideoCategories(
            Category="UnitTest Dog"
        )
        db.session.add(video_cat1)
        db.session.add(video_cat2)
        db.session.commit()
        self.valid_categories = [video_cat1.VideoCategoryID, video_cat2.VideoCategoryID]

        # Map Video 1 to two categories
        video1_mapping1 = VideosCategoriesMapping(
            VideoID=video1.VideoID,
            VideoCategoryID=video_cat1.VideoCategoryID
        )
        video1_mapping2 = VideosCategoriesMapping(
            VideoID=video1.VideoID,
            VideoCategoryID=video_cat2.VideoCategoryID
        )
        video2_mapping = VideosCategoriesMapping(
            VideoID=video2.VideoID,
            VideoCategoryID=video_cat1.VideoCategoryID
        )
        video3_mapping = VideosCategoriesMapping(
            VideoID=video3.VideoID,
            VideoCategoryID=video_cat2.VideoCategoryID
        )
        db.session.add(video1_mapping1)
        db.session.add(video1_mapping2)
        db.session.add(video2_mapping)
        db.session.add(video3_mapping)
        db.session.commit()
        self.valid_video_categories_video2 = [video2_mapping.VideoCategoryID]

        # We also need a valid admin user for the add release endpoint test.
        user = Users(
            Name="UnitTest Admin",
            Username="unittest",
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
        for video in Videos.query.filter(Videos.Title.like("UnitTest%")).all():
            db.session.delete(video)
        db.session.commit()

        # The mappings are cascade deleted when the related Video is removed.
        for c in VideoCategories.query.filter(VideoCategories.Category.like("UnitTest%")).all():
            db.session.delete(c)
        db.session.commit()

        user = Users.query.filter_by(UserID=self.user_id).first()
        db.session.delete(user)
        db.session.commit()

    def test_getting_all_videos(self):
        """Should return all videos in reverse chronological order."""
        response = self.app.get("/api/1.0/videos/")
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(data["videos"]))
        self.assertEqual("UnitTest Video 1", data["videos"][2]["title"])
        self.assertEqual("http://www.example.com/video1", data["videos"][2]["url"])
        self.assertEqual(
            [self.valid_categories[0], self.valid_categories[1]],
            data["videos"][2]["categories"]
        )
        self.assertNotEqual("", data["videos"][2]["createdAt"])

    def test_getting_one_video(self):
        """Should return the data of the specified video."""
        response = self.app.get("/api/1.0/videos/{}".format(self.valid_video_ids[1]))
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(data["videos"]))
        self.assertEqual("UnitTest Video 2", data["videos"][0]["title"])
        self.assertEqual("http://www.example.com/video2", data["videos"][0]["url"])
        self.assertEqual(
            [self.valid_video_categories_video2[0]],
            data["videos"][0]["categories"]
        )
        self.assertNotEqual("", data["videos"][0]["createdAt"])

    def test_adding_videos(self):
        """Should create a new entry to Videos and add the mapping."""
        response = self.app.post(
            "/api/1.0/videos/",
            data=json.dumps(
                dict(
                    title="UnitTest Post Video",
                    url="http://www.example.com/postvideo",
                    categories=[self.valid_categories[0], "UnitTest New Category"],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = json.loads(response.data.decode())

        video = Videos.query.filter_by(Title="UnitTest Post Video").first_or_404()
        cats = VideoCategories.query.filter_by(Category="UnitTest New Category").first_or_404()
        catmap = VideosCategoriesMapping.query.filter_by(VideoID=video.VideoID).all()

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertNotEqual(None, video)
        self.assertEqual("UnitTest Post Video", video.Title)
        self.assertEqual("http://www.example.com/postvideo", video.URL)

        self.assertNotEqual(None, cats)
        self.assertEqual("UnitTest New Category", cats.Category)

        self.assertEqual(2, len(catmap))
        self.assertTrue(self.valid_categories[0] in [c.VideoCategoryID for c in catmap])
        self.assertTrue(cats.VideoCategoryID in [c.VideoCategoryID for c in catmap])

    def test_updating_videos(self):
        """Should replace the existing data of the videos entry with the new data."""
        response = self.app.put(
            "/api/1.0/videos/{}".format(self.valid_video_ids[0]),
            data=json.dumps(
                dict(
                    title="UnitTest Updated Video",
                    url="http://www.example.com/unittest-update",
                    categories=[
                        self.valid_categories[0],
                        self.valid_categories[1],
                        "UnitTest New Cat from Update"
                    ],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = response.data.decode()

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[0]).first_or_404()
        cats = VideoCategories.query.filter_by(
            Category="UnitTest New Cat from Update"
        ).first_or_404()
        catmap = VideosCategoriesMapping.query.filter_by(VideoID=video.VideoID).all()

        self.assertEqual(200, response.status_code)
        self.assertEqual("", data)

        self.assertNotEqual(None, video)
        self.assertEqual("UnitTest Updated Video", video.Title)
        self.assertEqual("http://www.example.com/unittest-update", video.URL)
        self.assertNotEqual(None, video.Updated)

        self.assertNotEqual(None, cats)
        self.assertEqual("UnitTest New Cat from Update", cats.Category)

        self.assertEqual(3, len(catmap))
        self.assertTrue(self.valid_categories[0] in [c.VideoCategoryID for c in catmap])
        self.assertTrue(cats.VideoCategoryID in [c.VideoCategoryID for c in catmap])

    def test_updating_videos_using_invalid_category_id(self):
        """Should replace the existing data of the videos entry with the new data, but should
        skip the invalid category. Only the valid categories should be added."""
        response = self.app.put(
            "/api/1.0/videos/{}/".format(self.valid_video_ids[0]),
            data=json.dumps(
                dict(
                    title="UnitTest Updated Video",
                    url="http://www.example.com/unittest-update",
                    categories=[
                        self.valid_categories[0],
                        self.valid_categories[1],
                        "UnitTest New Cat from Update",
                        0
                    ],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[0]).first_or_404()
        catmap = VideosCategoriesMapping.query.filter_by(VideoID=video.VideoID).all()

        invalid = VideoCategories.query.filter_by(VideoCategoryID=0).first()

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(catmap))
        self.assertEqual(None, invalid)

    def test_updating_videos_using_existing_category_string(self):
        """Should replace the existing data of the videos entry with the new data, and should use
        the ID of the existing category string."""
        response = self.app.put(
            "/api/1.0/videos/{}".format(self.valid_video_ids[0]),
            data=json.dumps(
                dict(
                    title="UnitTest Updated Video",
                    url="http://www.example.com/unittest-update",
                    categories=[
                        self.valid_categories[0],
                        "UnitTest Dog"
                    ],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[0]).first_or_404()
        cats = VideoCategories.query.filter_by(Category="UnitTest Dog").all()
        catmap = VideosCategoriesMapping.query.filter_by(VideoID=video.VideoID).all()

        invalid = VideoCategories.query.filter_by(VideoCategoryID=0).first()

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(cats))
        self.assertEqual(2, len(catmap))
        self.assertEqual(None, invalid)

    def test_patching_videos_using_add(self):
        """Should replace the target value, if it is not empty. If empty, it will add the given
        value. In Categories, the new value should be appended to the existing mapping, if
        the new value is valid. If it is a new category, use the normal add_categories logic."""
        response = self.app.patch(
            "/api/1.0/videos/{}".format(self.valid_video_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "add",
                        "path": "/title",
                        "value": "UnitTest Patched Title"
                    }),
                    dict({
                        "op": "add",
                        "path": "/categories",
                        "value": [self.valid_categories[1]]
                    }),
                    dict({
                        "op": "add",
                        "path": "/categories",
                        "value": "UnitTest Patch Add Category"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = response.data.decode()

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[1]).first_or_404()
        cats = VideoCategories.query.filter_by(
            Category="UnitTest Patch Add Category"
        ).first_or_404()
        catmap = VideosCategoriesMapping.query.filter_by(VideoID=self.valid_video_ids[1]).all()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", data)
        self.assertEqual("UnitTest Patched Title", video.Title)
        self.assertNotEqual(None, cats)
        self.assertEqual("UnitTest Patch Add Category", cats.Category)
        # We have three categories for the video:
        # 1) the original, 2) the reference, and 3) the new added one
        self.assertEqual(3, len(catmap))
        self.assertTrue(cats.VideoCategoryID in [c.VideoCategoryID for c in catmap])

    def test_patching_videos_using_copy(self):
        cats_before_copy = VideosCategoriesMapping.query.filter_by(
            VideoID=self.valid_video_ids[2]).all()
        response = self.app.patch(
            "/api/1.0/videos/{}".format(self.valid_video_ids[2]),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/title",
                        "path": "/url"
                    }),
                    dict({
                        "op": "copy",
                        "from": "/categories",
                        "path": "/title"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = response.data.decode()

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[2]).first_or_404()
        cats_after_copy = VideosCategoriesMapping.query.filter_by(
            VideoID=self.valid_video_ids[2]).all()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", data)

        self.assertEqual("UnitTest Video 3", video.URL)
        self.assertEqual("UnitTest Video 3", video.Title)
        self.assertEqual(len(cats_before_copy), len(cats_after_copy))

    def test_patch_moving_categories(self):
        """Categories cannot be moved anywhere, so this should not do anything in the DB and it
        should return 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/videos/{}".format(self.valid_video_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "move",
                        "from": "/categories",
                        "path": "/title"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = response.data.decode()

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[1]).first()
        catmap = VideosCategoriesMapping.query.filter_by(VideoID=self.valid_video_ids[1]).all()

        self.assertEqual(204, response.status_code)
        self.assertEqual(1, len(catmap))
        self.assertEqual("", data)
        # Should not change
        self.assertEqual("UnitTest Video 2", video.Title)

    def test_patching_videos_using_replace(self):
        response = self.app.patch(
            "/api/1.0/videos/{}".format(self.valid_video_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/url",
                        "value": "UnitTest Test Replacement"
                    }),
                    dict({
                        "op": "replace",
                        "path": "/categories",
                        "value": [self.valid_categories[0], self.valid_categories[1]]
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = response.data.decode()

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[1]).first_or_404()
        cats = VideosCategoriesMapping.query.filter_by(VideoID=self.valid_video_ids[1]).all()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", data)
        self.assertEqual("UnitTest Test Replacement", video.URL)
        self.assertEqual(2, len(cats))

    def test_patching_videos_using_remove(self):
        """This should remove all video category mappings."""
        response = self.app.patch(
            "/api/1.0/videos/{}".format(self.valid_video_ids[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "remove",
                        "path": "/categories"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = response.data.decode()

        catmap = VideosCategoriesMapping.query.filter_by(VideoID=self.valid_video_ids[0]).all()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", data)
        self.assertEqual([], catmap)

    def test_patching_with_invalid_data(self):
        """Should return a 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/videos/{}".format(self.valid_video_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "move",
                        "from": "/doesnotexist",
                        "path": "/somerandom"
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = json.loads(response.data.decode())

        self.assertEqual(422, response.status_code)
        self.assertFalse(data["success"])

    def test_deleting_a_video(self):
        """Should remove the VIdeos entry and also the mappings related to it."""
        response = self.app.delete(
            "/api/1.0/videos/{}".format(self.valid_video_ids[0]),
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        data = response.data.decode()

        video = Videos.query.filter_by(VideoID=self.valid_video_ids[0]).first()
        catmap = VideosCategoriesMapping.query.filter_by(VideoID=self.valid_video_ids[0]).all()

        self.assertEqual(204, response.status_code)
        self.assertEqual(None, video)
        self.assertEqual(0, len(catmap))
        self.assertEqual("", data)
