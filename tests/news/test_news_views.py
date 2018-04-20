import json
import unittest

from sqlalchemy import asc

from app import app, db
from apps.news.models import News, NewsCategoriesMapping, NewsCategories
from apps.news.patches import patch_mapping
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestNewsView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # Add a dummy user - needed for NewsComments. No need to configure access levels here
        user = Users(
            Name="UnitTest",
            Username="unittester",
            Password="unittest",
            Created=get_datetime(),
        )
        db.session.add(user)
        db.session.commit()
        self.valid_user = user.UserID

        # Add some test news
        news1 = News(
            Title="UnitTest",
            Contents="UnitTest Contents",
            Author="UnitTest Author",
            Created=get_datetime(),
            Updated=get_datetime(),  # This is only to test "move" and "remove"
        )
        news2 = News(
            Title="UnitTest2",
            Contents="UnitTest2 Contents",
            Author="UnitTest2 Author",
            Created=get_datetime(),
        )
        db.session.add(news1)
        db.session.add(news2)
        db.session.commit()

        # Get the added news IDs
        self.news_ids = []
        added_news = News.query.filter(News.Title.like("UnitTest%")).all()

        # Add some News categories
        ncat1 = NewsCategories(
            Category="TestCategory1"
        )
        ncat2 = NewsCategories(
            Category="TestCategory2"
        )
        ncat3 = NewsCategories(
            Category="TestCategory3"
        )
        db.session.add(ncat1)
        db.session.add(ncat2)
        db.session.add(ncat3)
        db.session.commit()

        self.valid_news_cats = [ncat1.NewsCategoryID, ncat2.NewsCategoryID, ncat3.NewsCategoryID]

        # And create some Category mappings for them
        for news in added_news:
            self.news_ids.append(news.NewsID)
            cat1 = NewsCategoriesMapping(
                NewsID=news.NewsID,
                NewsCategoryID=self.valid_news_cats[0],
            )
            cat2 = NewsCategoriesMapping(
                NewsID=news.NewsID,
                NewsCategoryID=self.valid_news_cats[2],
            )
            db.session.add(cat1)
            db.session.add(cat2)
            db.session.commit()

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
        # Delete news items created for the unittest
        for news in News.query.all():
            db.session.delete(news)

        # Delete news categories
        for cat in NewsCategories.query.all():
            db.session.delete(cat)

        # Delete user created for the unittest
        for user in Users.query.all():
            db.session.delete(user)
        db.session.commit()

    def test_getting_all_news(self):
        response = self.app.get("/api/1.0/news/")
        news = json.loads(
            response.get_data().decode()
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len([n for n in news["news"]]))
        self.assertEquals("UnitTest", news["news"][0]["title"])
        self.assertEquals(2, len(news["news"][0]["categories"]))
        self.assertTrue("TestCategory1" in news["news"][0]["categories"])
        self.assertTrue("TestCategory3" in news["news"][1]["categories"])

    def test_getting_one_news(self):
        response = self.app.get("/api/1.0/news/{}".format(int(self.news_ids[1])))
        news = json.loads(
            response.get_data().decode()
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest2", news["news"][0]["title"])
        self.assertEquals(2, len(news["news"][0]["categories"]))
        self.assertTrue("TestCategory1" in news["news"][0]["categories"])
        self.assertTrue("TestCategory3" in news["news"][0]["categories"])

    def test_adding_news(self):
        response = self.app.post(
            "/api/1.0/news/",
            data=json.dumps(
                dict(
                    title="UnitTest Post",
                    contents="UnitTest",
                    author="UnitTester",
                    categories=[
                        self.valid_news_cats[0],
                        self.valid_news_cats[2],
                        "TestCategoryNew",
                        "",  # Empty values should be skipped,
                        "TestCategory1"  # Existing values should be reused
                    ],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        news = News.query.filter_by(Title="UnitTest Post").first_or_404()
        cats = NewsCategoriesMapping.query.filter_by(NewsID=news.NewsID).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)).all()
        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest", news.Contents)
        self.assertEquals(3, len(cats))
        # When a new non-existing string category is given,
        # it should be added to general NewsCategories
        new_cat = NewsCategories.query.filter_by(Category="TestCategoryNew").first_or_404()
        self.assertEquals("TestCategoryNew", new_cat.Category)

    def test_adding_news_with_string_categories(self):
        """If a string of categories is given, it should be split into a list by commas."""
        response = self.app.post(
            "/api/1.0/news/",
            data=json.dumps(
                dict(
                    title="UnitTest Post",
                    contents="UnitTest",
                    author="UnitTester",
                    categories="{}, {}, {}, {}, {}".format(
                        self.valid_news_cats[0],
                        self.valid_news_cats[2],
                        "TestCategoryNew",
                        "",  # Empty values should be skipped,
                        "TestCategory1"  # Existing values should be reused
                    ),
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        news = News.query.filter_by(Title="UnitTest Post").first_or_404()
        cats = NewsCategoriesMapping.query.filter_by(NewsID=news.NewsID).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)).all()
        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest", news.Contents)
        # Should be 3 out of 5, because one item is an empty string, and one is pre-existing
        self.assertEquals(3, len(cats))
        # When a new non-existing string category is given,
        # it should be added to general NewsCategories
        new_cat = NewsCategories.query.filter_by(Category="TestCategoryNew").first_or_404()
        self.assertEquals("TestCategoryNew", new_cat.Category)

    def test_deleting_news(self):
        response = self.app.delete(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        query_result = News.query.filter_by(NewsID=self.news_ids[0]).first()
        # On delete cascade should also remove the categories of the news ID
        cats = NewsCategoriesMapping.query.filter_by(NewsID=self.news_ids[0]).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals(None, query_result)
        self.assertEquals([], cats)

    def test_putting_things(self):
        response = self.app.put(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                dict(
                    title="UnitTest Put Title",
                    contents="UnitTest Put Contents",
                    author="UnitTest Put Author",
                    categories=[4, 5],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        news = News.query.get_or_404(self.news_ids[0])
        cats = NewsCategoriesMapping.query.filter_by(NewsID=self.news_ids[0]).all()

        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest Put Title", news.Title)
        self.assertEquals("UnitTest Put Contents", news.Contents)
        self.assertEquals("UnitTest Put Author", news.Author)
        self.assertEquals(2, len(cats))
        self.assertEquals(4, cats[0].NewsCategoryID)

    def test_patch_mapping(self):
        patch = [
            {"op": "add", "path": "/title", "value": "testi"},
            {"op": "copy", "from": "/author", "path": "/contents"},
            {"op": "remove", "path": "/contents"},
            {"op": "replace", "path": "/categories", "value": [2, 3]},
        ]

        mapped_patchdata = []
        for p in patch:
            p = patch_mapping(p)
            mapped_patchdata.append(p)

        self.assertEquals(4, len(mapped_patchdata))
        self.assertEquals("add", mapped_patchdata[0]["op"])
        self.assertEquals("/Title", mapped_patchdata[0]["path"])
        self.assertEquals("testi", mapped_patchdata[0]["value"])
        self.assertEquals("/Author", mapped_patchdata[1]["from"])
        self.assertEquals("/Contents", mapped_patchdata[1]["path"])
        self.assertEquals("/Contents", mapped_patchdata[2]["path"])
        self.assertEquals("/NewsCategoryID", mapped_patchdata[3]["path"])

    """
    The below tests run various PATCH cases, as defined:

    The RFC 6902 defines a Patch JSON like this (the order of "op" does not matter):
    [
        { "op": "add", "path": "/a/b/c", "value": [ "foo", "bar" ] },
        { "op": "copy", "from": "/a/b/d", "path": "/a/b/e" }
        { "op": "move", "from": "/a/b/c", "path": "/a/b/d" },
        { "op": "remove", "path": "/a/b/c" },
        { "op": "replace", "path": "/a/b/c", "value": 42 },
        { "op": "test", "path": "/a/b/c", "value": "foo" },
    ]

    All have been implemented, but in practice I doubt we'll use anything else than "add" and
    "replace"
    """

    def test_patching_things_using_add(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/title",
                        value="UnitTest Patched Title",
                    ),
                    dict(
                        op="add",
                        path="/author",
                        value="UnitTest Patched Author",
                    ),
                    dict(
                        op="add",
                        path="/categories",
                        value=[2],
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        news = News.query.get_or_404(self.news_ids[0])
        cats = NewsCategoriesMapping.query.filter_by(NewsID=self.news_ids[0]).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest Patched Title", news.Title)
        self.assertEquals("UnitTest Patched Author", news.Author)
        self.assertEquals(3, len(cats))
        # Since the PATCH defined a specific ID, we check for it instead of self.valid_news_cats
        self.assertEquals(2, cats[0].NewsCategoryID)
        self.assertEquals(self.valid_news_cats[0], cats[1].NewsCategoryID)
        self.assertEquals(self.valid_news_cats[2], cats[2].NewsCategoryID)

    def test_patching_things_using_copy(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[1])),
            data=json.dumps(
                [{
                    "op": "copy",
                    "from": "/contents",  # Cannot use from in a dict. It is a keyword
                    "path": "/author"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        news = News.query.get_or_404(self.news_ids[1])

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest2 Contents", news.Author)

    def test_patching_things_using_move(self):
        """NOTE! More than half the columns in this project are nullable=False, which prevents
        "move" and "remove" from making the old value NULL :)
        In the News model, only Updated is nullable=True"""
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/updated",  # Cannot use from in a dict. It is a keyword
                    "path": "/author"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(204, response.status_code)
        self.assertNotEquals("UnitTest Author", news.Author)

    def test_patching_news_using_remove(self):
        """NOTE! More than half the columns in this project are nullable=False, which prevents
        "move" and "remove" from making the old value NULL :)
        In the News model, only Updated is nullable=True.

        For News Categories, there is a special separate method that does support remove, because
        it is a common thing to do."""
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/updated"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(204, response.status_code)

    def test_patching_categories_using_remove(self):
        """For News Categories, there is a special separate method that does support remove, because
        it is a common thing to do."""
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/categories"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        cats = NewsCategoriesMapping.query.filter_by(NewsID=self.news_ids[0]).all()
        self.assertEquals(response.status_code, 204)
        self.assertEquals([], cats)

    def test_patching_categories_using_copy(self):
        """For News Categories, the "copy" patch has no meaning, as there is nowhere to copy to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "copy",
                    "from": "/categories",
                    "path": "/categories"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_categories_using_move(self):
        """For News Categories, the "move" patch has no meaning, as there is nowhere to move to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/categories",
                    "path": "/categories"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_things_using_replace(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "replace",
                    "path": "/author",
                    "value": "UnitTest Patch Replace"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest Patch Replace", news.Author)

    def test_patching_things_using_test_with_nonexisting_path(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[1])),
            data=json.dumps(
                [{
                    "op": "test",
                    "path": "/doesnotexist",
                    "value": "I do not exist"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(422, response.status_code)
        self.assertFalse("", response.data.decode())

    def test_category_patch_replace(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(self.news_ids[0]),
            data=json.dumps(
                [{
                    "op": "replace",
                    "path": "/categories",
                    "value": [4, 5]
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        cats = NewsCategoriesMapping.query.filter_by(NewsID=self.news_ids[0]).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)
        ).all()

        self.assertEquals(204, response.status_code)
        self.assertFalse("", response.data.decode())
        self.assertEquals(2, len(cats))
        self.assertEquals(4, cats[0].NewsCategoryID)
        self.assertEquals(5, cats[1].NewsCategoryID)
