import json
import unittest

from flask_caching import Cache

from app import app, db
from apps.photos.models import PhotoCategories


class TestPhotoCategories(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "RedisCache"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()
        # Add some categories
        cat1 = PhotoCategories(
            Category="testCategory1"
        )
        cat2 = PhotoCategories(
            Category="testCategory2"
        )
        cat3 = PhotoCategories(
            Category="testCategory3"
        )
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.commit()
        self.valid_cats = [cat1.PhotoCategoryID, cat2.PhotoCategoryID, cat3.PhotoCategoryID]

    def tearDown(self):
        try:
            for cat in PhotoCategories.query.all():
                db.session.delete(cat)
            db.session.commit()
        except TypeError as e:
            print("Teardown failed:\n{}".format(e))

    def test_get_photo_categories(self):
        """Should return all valid photo categories and the IDs."""
        response = self.app.get("/api/1.0/photos/categories/")
        categories = json.loads(
            response.get_data().decode()
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(categories["photoCategories"]))
        self.assertEqual(self.valid_cats[0], categories["photoCategories"][0]["id"])
        self.assertEqual("testCategory1", categories["photoCategories"][0]["category"])
        self.assertEqual(self.valid_cats[2], categories["photoCategories"][2]["id"])
        self.assertEqual("testCategory3", categories["photoCategories"][2]["category"])
