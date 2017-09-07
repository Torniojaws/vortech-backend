import json
import unittest
import time

from app import app, db
from apps.news.models import News


class TestNewsView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # Add some test news
        news1 = News(
            Title="UnitTest",
            Contents="UnitTest Contents",
            Author="UnitTest Author",
            Created=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        news2 = News(
            Title="UnitTest2",
            Contents="UnitTest2 Contents",
            Author="UnitTest2 Author",
            Created=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(news1)
        db.session.add(news2)
        db.session.commit()

        # Get their IDs
        self.news_ids = []
        added_news = News.query.filter(News.Title.like("UnitTest%")).all()
        for news in added_news:
            self.news_ids.append(news.NewsID)

    def tearDown(self):
        to_delete = News.query.filter(News.Title.like("UnitTest%")).all()
        for news in to_delete:
            db.session.delete(news)
        db.session.commit()

    def test_getting_all_news(self):
        response = self.app.get("/api/1.0/news/")
        news = json.loads(
            response.get_data().decode()
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len([n for n in news["news"]]))
        self.assertEquals("UnitTest", news["news"][0]["title"])

    def test_getting_one_news(self):
        response = self.app.get("/api/1.0/news/{}".format(int(self.news_ids[1])))
        news = json.loads(
            response.get_data().decode()
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest2", news["news"][0]["title"])

    def test_adding_news(self):
        response = self.app.post(
            "/api/1.0/news/",
            data=json.dumps(
                dict(
                    title="UnitTest Post",
                    contents="UnitTest",
                    author="UnitTester"
                )
            ),
            content_type="application/json"
        )
        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())

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
    """

    def test_patching_things_using_add(self):
        # TODO: How to make the "path" case-insensitive, since the DB column is eg. News.Title
        # With path "/title" it fails, and with path "/Title" it works
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/Title",
                        value="UnitTest Patched Title",
                    )
                ]
            ),
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest Patched Title", news.Title)

    """
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
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/contents",  # Cannot use from in a dict. It is a keyword
                    "path": "/author"
                }]
            ),
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest2 Contents", news.Author)
        self.assertEquals(None, news.Contents)  # Move is identical to replace+remove

    def test_patching_things_using_remove(self):
        response = self.app.patch(
            "/api/1.0/news/{}".format(int(self.news_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/author"
                }]
            ),
            content_type="application/json"
        )

        news = News.query.get_or_404(self.news_ids[0])

        self.assertEquals(200, response.status_code)
        self.assertEquals(None, news.Author)

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

        self.assertEquals(200, response.status_code)
        self.assertFalse(response.data)
    """
