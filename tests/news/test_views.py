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
            Contents="UnitTest",
            Author="UnitTest",
            Created=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        news2 = News(
            Title="UnitTest2",
            Contents="UnitTest2",
            Author="UnitTest2",
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
            content_type='application/json'
        )
        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())

    def test_deleting_news(self):
        response = self.app.delete("/api/1.0/news/{}".format(int(self.news_ids[0])))
        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
