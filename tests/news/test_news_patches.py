import json
import unittest

from sqlalchemy import asc

from app import db
from apps.news.patches import patch_item, get_value
from apps.news.models import News, NewsCategories, NewsCategoriesMapping
from apps.utils.time import get_datetime


class TestNewsPatches(unittest.TestCase):
    def setUp(self):
        self.created = get_datetime()
        self.updated = get_datetime()
        item1 = News(
            Title="Test News 1",
            Contents="My news 1",
            Author="UnitTester",
            Created=self.created
        )
        db.session.add(item1)
        item2 = News(
            Title="Test News 2",
            Contents="My news 2",
            Author="UnitTester",
            Created=self.created,
            Updated=self.updated,
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

    def test_simple_patch(self):
        payload = json.dumps([
            {"op": "add", "path": "/title", "value": "New title"}
        ])
        result = patch_item(self.valid_news_id[0], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[0]).first()
        self.assertEqual("New title", result["title"])
        self.assertEqual("New title", news_item.Title)

    def test_multiple_patches(self):
        payload = json.dumps([
            {"op": "add", "path": "/title", "value": "Multi title"},
            {"op": "add", "path": "/author", "value": "Multiple author"},
            {"op": "copy", "from": "/contents", "path": "/author"},
            {"op": "remove", "path": "/updated"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[1]).first()
        self.assertEqual("Multi title", result["title"])
        self.assertEqual("My news 2", result["author"])
        self.assertEqual(None, result["updated"])
        self.assertEqual("Multi title", news_item.Title)
        self.assertEqual("My news 2", news_item.Author)
        self.assertNotEqual(None, news_item.Updated)  # Populated at the end of a PATCH

    def test_less_common_patches(self):
        payload = json.dumps([
            {"op": "move", "from": "/updated", "path": "/contents"},
            {"op": "test", "path": "/title", "value": "Test News 2"},
            {"op": "replace", "path": "/author", "value": "New Author"},
            {"op": "remove", "path": "/categories"},
            {"op": "copy", "from": "/author", "path": "/title"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[1]).first()
        news_cats = NewsCategoriesMapping.query.filter_by(NewsID=self.valid_news_id[1]).all()

        self.assertNotEqual("My news 2", result["contents"])
        self.assertEqual([], result["categories"])
        self.assertEqual(0, len(news_cats))
        self.assertEqual("New Author", result["author"])
        self.assertEqual("New Author", result["title"])
        self.assertNotEqual(None, news_item.Updated)  # Populated at the end of a PATCH

    def test_news_categories(self):
        """When adding news categories, we currently assume an integer list, ie. already existing
        categories. There might be strings later, which would be checked if they already exist.
        If not, they would be added and then their ID reference would be used."""
        payload = json.dumps([
            {"op": "add", "path": "/categories", "value": [
                self.valid_cat_ids[1], self.valid_cat_ids[2]
            ]},
        ])
        result = patch_item(self.valid_news_id[0], payload)
        news_cats = NewsCategoriesMapping.query.filter_by(NewsID=self.valid_news_id[0]).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)
        ).all()
        self.assertEqual(3, len(news_cats))
        self.assertEqual(sorted(self.valid_cat_ids), sorted(result["categories"]))

    def test_copy_date_updated(self):
        payload = json.dumps([
            {"op": "copy", "from": "/updated", "path": "/created"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[1]).first()

        self.assertEqual(self.updated, result["created"])
        self.assertEqual(self.updated, news_item.Updated.strftime("%Y-%m-%d %H:%M:%S"))

    def test_copy_date_created(self):
        payload = json.dumps([
            {"op": "copy", "from": "/created", "path": "/updated"},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        news_item = News.query.filter_by(NewsID=self.valid_news_id[1]).first()

        self.assertEqual(self.created, result["updated"])
        self.assertEqual(self.created, news_item.Updated.strftime("%Y-%m-%d %H:%M:%S"))

    def test_replacing_news_categories(self):
        """When replacing news categories, we currently assume an integer list, ie. already existing
        categories. There might be strings later, which would be checked if they already exist.
        If not, they would be added and then their ID reference would be used."""
        payload = json.dumps([
            {"op": "replace", "path": "/categories", "value": [
                self.valid_cat_ids[1], self.valid_cat_ids[2]
            ]},
        ])
        result = patch_item(self.valid_news_id[0], payload)
        news_cats = NewsCategoriesMapping.query.filter_by(NewsID=self.valid_news_id[0]).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)
        ).all()
        self.assertEqual(2, len(news_cats))
        self.assertEqual(
            sorted([self.valid_cat_ids[1], self.valid_cat_ids[2]]),
            sorted(result["categories"])
        )

    def test_test_op(self):
        """The test op returns a boolean whether the test value matches target."""
        payload = json.dumps([
            {"op": "test", "path": "/title", "value": "Test News 2"},
            {"op": "test", "path": "/contents", "value": "My news 2"},
            {"op": "test", "path": "/author", "value": "UnitTester"},
            {"op": "test", "path": "/created", "value": self.created},
            {"op": "test", "path": "/updated", "value": self.updated},
        ])
        result = patch_item(self.valid_news_id[1], payload)
        # If only "test" ops are run, an empty object is returned. Non-matches would raise.
        self.assertEqual({}, result)

    def test_getting_values(self):
        """Should return the value of the path."""
        news_item = News.query.filter_by(NewsID=self.valid_news_id[1]).first()
        self.assertEqual("Test News 2", get_value(news_item, "/title"))
        self.assertEqual("UnitTester", get_value(news_item, "/author"))
        self.assertEqual(self.created, get_value(news_item, "/created"))
        self.assertEqual("", get_value(news_item, "/doesnotexist"))
