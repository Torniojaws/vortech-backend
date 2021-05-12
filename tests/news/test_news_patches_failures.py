import json
import unittest

from app import db
from apps.news.patches import (
    patch_item, add, copy, move, remove, replace
)
from apps.news.models import News, NewsCategories, NewsCategoriesMapping
from apps.utils.time import get_datetime


class TestNewsPatchesFailures(unittest.TestCase):
    def setUp(self):
        item1 = News(
            Title="Test News 1",
            Contents="My news 1",
            Author="UnitTester",
            Created=get_datetime()
        )
        db.session.add(item1)
        item2 = News(
            Title="Test News 2",
            Contents="My news 2",
            Author="UnitTester",
            Created=get_datetime(),
            Updated=get_datetime(),
        )
        db.session.add(item2)
        db.session.commit()
        self.valid_news_id = [item1.NewsID, item2.NewsID]

        # Make sure we have no categories mapped
        for catmap in NewsCategoriesMapping.query.all():
            db.session.delete(catmap)
        for cat in NewsCategories.query.all():
            db.session.delete(cat)
        db.session.commit()

        # Add some valid news categories
        cat1 = NewsCategories(Category="UnitTest1")
        cat2 = NewsCategories(Category="UnitTest2")
        cat3 = NewsCategories(Category="UnitTest3")
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.commit()

        # And map the first category to both News items
        newscat1 = NewsCategoriesMapping(
            NewsID=item1.NewsID,
            NewsCategoryID=cat1.NewsCategoryID
        )
        newscat2 = NewsCategoriesMapping(
            NewsID=item2.NewsID,
            NewsCategoryID=cat1.NewsCategoryID
        )
        db.session.add(newscat1)
        db.session.add(newscat2)
        db.session.commit()
        self.valid_cat_ids = [
            cat1.NewsCategoryID, cat2.NewsCategoryID, cat3.NewsCategoryID
        ]

    def tearDown(self):
        for news in News.query.all():
            db.session.delete(news)
        for cat in NewsCategoriesMapping.query.all():
            db.session.delete(cat)
        for catmap in NewsCategories.query.all():
            db.session.delete(catmap)
        db.session.commit()

    def test_news_categories_with_invalid_data(self):
        payload = json.dumps([[{"op": "add", "path": "/categories", "value": "invalid"}]])
        result = patch_item(self.valid_news_id[0], payload)
        self.assertFalse(result["success"])
        self.assertEqual("Only lists are allowed in categories", result["message"])

    def test_db_constraint(self):
        """When attempting an operation that is against the DB constraints."""
        payload = json.dumps([
            {"op": "move", "from": "/author", "path": "/title"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[0]).first()
        self.assertNotEqual(None, news_item.Author)
        self.assertFalse(result["success"])
        self.assertEqual("The defined source cannot be nullified (NOT NULL)", result["message"])

    def test_failing_test_op(self):
        """When the test OP comparison fails, should cancel the patch and rollback any
        commits that were created before the OP."""
        payload = json.dumps([
            {"op": "add", "path": "/contents", "value": "Should not change"},
            {"op": "replace", "path": "/author", "value": "Should not change"},
            {"op": "test", "path": "/title", "value": "not the same value"},
            {"op": "move", "from": "/updated", "path": "/title"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[1]).first()
        self.assertNotEqual("Should not change", news_item.Contents)
        self.assertNotEqual("Should not change", news_item.Author)
        self.assertEqual("Test News 2", news_item.Title)
        self.assertFalse(result["success"])
        self.assertEqual("Comparison test failed in the patch", result["message"])

    def test_invalid_op(self):
        """When an invalid OP is in the payload, should cancel the patch and rollback any
        commits that were created before the OP."""
        payload = json.dumps([
            {"op": "replace", "path": "/author", "value": "Should not change"},
            {"op": "invalid", "from": "/updated", "path": "/contents"}
        ])
        result = patch_item(self.valid_news_id[0], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[0]).first()
        self.assertNotEqual("Should not change", news_item.Author)
        self.assertFalse(result["success"])
        self.assertEqual("Invalid operation in patch", result["message"])

    def test_add_function_with_non_list(self):
        """Should raise a ValueError."""
        with self.assertRaises(ValueError):
            add(None, "/categories", "Not-List", {})

    def test_copying_to_categories_raises(self):
        """Technically it is a valid operation, but we prevent it."""
        with self.assertRaises(ValueError):
            copy(None, "/author", "/categories", {})

    def test_moving_to_categories_raises(self):
        """Technically it is a valid operation, but we prevent it."""
        with self.assertRaises(Exception):
            move(None, "/author", "/categories", {})

    def test_removing_constrainted_items_raises(self):
        """Technically it is a valid operation, but we prevent it."""
        with self.assertRaises(ValueError):
            remove(None, "/author", {})

    def test_replacing_categories_with_non_list_raises(self):
        """Technically it is a valid operation, but we prevent it."""
        with self.assertRaises(ValueError):
            replace(None, "/categories", "not-allowed", {})

    def test_test_op_with_invalid_path(self):
        """The test op returns a boolean whether the test value matches target."""
        payload = json.dumps([
            {"op": "test", "path": "/doesnotexist", "value": "Test News 2"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        self.assertEqual(False, result["success"])
        self.assertEqual("Comparison test failed in the patch", result["message"])

    def test_copy_to_unknown_target_raises(self):
        payload = json.dumps([
            {"op": "copy", "from": "/created", "path": "/doesnotexist"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        self.assertEqual(False, result["success"])
        self.assertEqual("Invalid operation in patch", result["message"])
