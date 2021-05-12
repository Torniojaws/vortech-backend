import json
import unittest

from flask_caching import Cache

from app import app, db
from apps.releases.models import ReleaseCategories


class TestReleaseCategories(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "RedisCache"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()
        # Add some categories
        cat1 = ReleaseCategories(
            ReleaseCategory="testCategory1"
        )
        cat2 = ReleaseCategories(
            ReleaseCategory="testCategory2"
        )
        cat3 = ReleaseCategories(
            ReleaseCategory="testCategory3"
        )
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.commit()
        self.valid_cats = [cat1.ReleaseCategoryID, cat2.ReleaseCategoryID, cat3.ReleaseCategoryID]

    def tearDown(self):
        try:
            for cat in ReleaseCategories.query.all():
                db.session.delete(cat)
            db.session.commit()
        except TypeError as e:
            print("Teardown failed:\n{}".format(e))

    def test_get_release_categories(self):
        """Should return all valid release categories and the IDs."""
        response = self.app.get("/api/1.0/releases/categories/")
        categories = json.loads(
            response.get_data().decode()
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(categories["releaseCategories"]))
        self.assertEqual(self.valid_cats[0], categories["releaseCategories"][0]["id"])
        self.assertEqual("testCategory1", categories["releaseCategories"][0]["category"])
        self.assertEqual(self.valid_cats[2], categories["releaseCategories"][2]["id"])
        self.assertEqual("testCategory3", categories["releaseCategories"][2]["category"])
