import json
import unittest

from flask_caching import Cache

from app import app, db
from apps.shop.models import ShopCategories


class TestShopCategories(unittest.TestCase):
    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()
        # Add some categories
        cat1 = ShopCategories(
            Category="testCategory1",
            SubCategory="testSubcat1"
        )
        cat2 = ShopCategories(
            Category="testCategory2",
            SubCategory="testSubcat2"
        )
        cat3 = ShopCategories(
            Category="testCategory3",
            SubCategory="testSubcat3"
        )
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.commit()
        self.valid_cats = [cat1.ShopCategoryID, cat2.ShopCategoryID, cat3.ShopCategoryID]

    def tearDown(self):
        try:
            for cat in ShopCategories.query.all():
                db.session.delete(cat)
            db.session.commit()
        except TypeError as e:
            print("Teardown failed:\n{}".format(e))

    def test_get_shop_categories(self):
        """Should return all valid shop categories, subcategories and the IDs."""
        response = self.app.get("/api/1.0/shopitems/categories/")
        categories = json.loads(
            response.get_data().decode()
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals(3, len(categories["shopCategories"]))
        self.assertEquals(self.valid_cats[0], categories["shopCategories"][0]["id"])
        self.assertEquals("testCategory1", categories["shopCategories"][0]["category"])
        self.assertEquals("testSubcat1", categories["shopCategories"][0]["subCategory"])
        self.assertEquals(self.valid_cats[2], categories["shopCategories"][2]["id"])
        self.assertEquals("testCategory3", categories["shopCategories"][2]["category"])
        self.assertEquals("testSubcat3", categories["shopCategories"][2]["subCategory"])
