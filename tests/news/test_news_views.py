import json
import unittest

from sqlalchemy import asc

from app import app, db
from apps.news.models import News, NewsCategoriesMapping, NewsComments
from apps.users.models import Users
from apps.utils.time import get_datetime


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

        # And create some Category mappings and comments for them
        for news in added_news:
            self.news_ids.append(news.NewsID)
            cat1 = NewsCategoriesMapping(
                NewsID=news.NewsID,
                NewsCategoryID=1,
            )
            cat2 = NewsCategoriesMapping(
                NewsID=news.NewsID,
                NewsCategoryID=3,
            )
            comment1 = NewsComments(
                NewsID=news.NewsID,
                UserID=self.valid_user,
                Comment="UnitTest Comment for news {}".format(news.NewsID),
                Created=get_datetime(),
            )
            comment2 = NewsComments(
                NewsID=news.NewsID,
                UserID=self.valid_user,
                Comment="UnitTest Another Comment for news {}".format(news.NewsID),
                Created=get_datetime(),
            )
            db.session.add(cat1)
            db.session.add(cat2)
            db.session.add(comment1)
            db.session.add(comment2)
            db.session.commit()

        # Get the added news comment IDs
        comments = NewsComments.query.filter(
            NewsComments.Comment.like("UnitTest%")
        ).order_by(
            asc(NewsComments.NewsCommentID)
        ).all()
        self.news_comments = [nc.NewsCommentID for nc in comments]

    def tearDown(self):
        # Delete news items created for the unittest
        to_delete = News.query.filter(News.Title.like("UnitTest%")).all()
        for news in to_delete:
            db.session.delete(news)

        # Delete news comments created for the unittest
        delete_comments = NewsComments.query.filter(NewsComments.Comment.like("UnitTest%")).all()
        for comment in delete_comments:
            db.session.delete(comment)

        # Delete user created for the unittest
        delete_user = Users.query.filter(Users.Name == "UnitTest").all()
        for user in delete_user:
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
        self.assertEquals(3, news["news"][0]["categories"][1])

    def test_getting_one_news(self):
        response = self.app.get("/api/1.0/news/{}".format(int(self.news_ids[1])))
        news = json.loads(
            response.get_data().decode()
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest2", news["news"][0]["title"])
        self.assertEquals(2, len(news["news"][0]["categories"]))
        self.assertEquals(3, news["news"][0]["categories"][1])

    def test_adding_news(self):
        response = self.app.post(
            "/api/1.0/news/",
            data=json.dumps(
                dict(
                    title="UnitTest Post",
                    contents="UnitTest",
                    author="UnitTester",
                    categories=[1, 3],
                )
            ),
            content_type="application/json"
        )
        news = News.query.filter_by(Title="UnitTest Post").first_or_404()
        cats = NewsCategoriesMapping.query.filter_by(NewsID=news.NewsID).order_by(
            asc(NewsCategoriesMapping.NewsCategoryID)).all()
        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest", news.Contents)
        self.assertEquals(2, len(cats))
        self.assertEquals(3, cats[1].NewsCategoryID)

    def test_deleting_news(self):
        response = self.app.delete("/api/1.0/news/{}".format(int(self.news_ids[0])))
        query_result = News.query.filter_by(NewsID=self.news_ids[0]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals(None, query_result)

    def test_putting_things(self):
        response = self.app.put(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                dict(
                    title="UnitTest Put Title",
                    contents="UnitTest Put Contents",
                    author="UnitTest Put Author",
                )
            ),
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest Put Title", news.Title)
        self.assertEquals("UnitTest Put Contents", news.Contents)
        self.assertEquals("UnitTest Put Author", news.Author)

    def test_patch_mapping(self):
        from apps.news.views import NewsView
        news = NewsView()

        patch = [
            {"op": "add", "path": "/title", "value": "testi"},
            {"op": "copy", "from": "/author", "path": "/contents"},
            {"op": "remove", "path": "/contents"}
        ]

        mapped_patchdata = []
        for p in patch:
            p = news.patch_mapping(p)
            mapped_patchdata.append(p)

        self.assertEquals(3, len(mapped_patchdata))
        self.assertEquals("add", mapped_patchdata[0]["op"])
        self.assertEquals("/Title", mapped_patchdata[0]["path"])
        self.assertEquals("testi", mapped_patchdata[0]["value"])
        self.assertEquals("/Author", mapped_patchdata[1]["from"])
        self.assertEquals("/Contents", mapped_patchdata[1]["path"])
        self.assertEquals("/Contents", mapped_patchdata[2]["path"])

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
                    )
                ]
            ),
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest Patched Title", news.Title)
        self.assertEquals("UnitTest Patched Author", news.Author)

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
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[1])

        self.assertEquals(200, response.status_code)
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
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(200, response.status_code)
        self.assertNotEquals("UnitTest Author", news.Author)
        # NB: The below cannot be done, because in jsonpatch the value is fully removedself.
        # self.assertEquals(None, news.Updated)

    def test_patching_things_using_remove(self):
        """NOTE! More than half the columns in this project are nullable=False, which prevents
        "move" and "remove" from making the old value NULL :)
        In the News model, only Updated is nullable=True"""
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/updated"
                }]
            ),
            content_type="application/json"
        )

        self.assertEquals(200, response.status_code)
        # NB: This cannot be done with jsonpatch.
        # See https://github.com/stefankoegl/python-json-patch/issues/70
        # self.assertEquals(None, news.Updated)

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
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest Patch Replace", news.Author)

    def test_patching_things_using_test_with_existing_value(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[1])),
            data=json.dumps(
                [{
                    "op": "test",
                    "path": "/author",
                    "value": "UnitTest2 Author"
                }]
            ),
            content_type="application/json"
        )

        self.assertEquals(200, response.status_code)
        self.assertTrue(response.data)

    def test_patching_things_using_test_with_nonexisting_value(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[1])),
            data=json.dumps(
                [{
                    "op": "test",
                    "path": "/contents",
                    "value": "I do not exist"
                }]
            ),
            content_type="application/json"
        )
        resp = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertFalse(resp["success"])

    def test_getting_specific_news_comment(self):
        response = self.app.get(
            "/api/1.0/news/{}/comments/{}".format(
                int(self.news_ids[0]),
                int(self.news_comments[0]),
            )
        )
        resp = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(resp["comments"]))
        self.assertEquals(
            "UnitTest Comment for news {}".format(self.news_ids[0]),
            resp["comments"][0]["comment"]
        )

    def test_getting_all_news_comments_for_a_news(self):
        response = self.app.get(
            "/api/1.0/news/{}/comments/".format(self.news_ids[0])
        )
        resp = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len(resp["comments"]))
        self.assertEquals(
            "UnitTest Comment for news {}".format(self.news_ids[0]),
            resp["comments"][0]["comment"]
        )
        self.assertEquals(
            "UnitTest Another Comment for news {}".format(self.news_ids[0]),
            resp["comments"][1]["comment"]
        )
