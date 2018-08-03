import json
import unittest

from flask_caching import Cache

from app import app, db
from apps.videos.models import VideoCategories


class TestVideoCategories(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()
        # Add some categories
        cat1 = VideoCategories(
            Category="testCategory1"
        )
        cat2 = VideoCategories(
            Category="testCategory2"
        )
        cat3 = VideoCategories(
            Category="testCategory3"
        )
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.commit()
        self.valid_cats = [cat1.VideoCategoryID, cat2.VideoCategoryID, cat3.VideoCategoryID]

    def tearDown(self):
        try:
            for cat in VideoCategories.query.all():
                db.session.delete(cat)
            db.session.commit()
        except TypeError as e:
            print("Teardown failed:\n{}".format(e))

    def test_get_video_categories(self):
        """Should return all valid video categories and the IDs."""
        response = self.app.get("/api/1.0/videos/categories/")
        categories = json.loads(
            response.get_data().decode()
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals(3, len(categories["videoCategories"]))
        self.assertEquals(self.valid_cats[0], categories["videoCategories"][0]["id"])
        self.assertEquals("testCategory1", categories["videoCategories"][0]["category"])
        self.assertEquals(self.valid_cats[2], categories["videoCategories"][2]["id"])
        self.assertEquals("testCategory3", categories["videoCategories"][2]["category"])
