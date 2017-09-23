import unittest

from app import app, db
from apps.biography.models import Biography
from apps.utils.time import get_datetime


class TestBiographyViews(unittest.TestCase):
    def setUp(self):
        """Add some test entries to the database, so we can test getting the latest one."""
        self.app = app.test_client()

        entry1 = Biography(
            Short="This is the first Biography entry.",
            Full="This is the first longer entry in the Biographies.",
            Created=get_datetime(),
        )
        entry2 = Biography(
            Short="This is the first Biography entry.",
            Full="This is the first longer entry in the Biographies.",
            Created=get_datetime(),
        )
        entry3 = Biography(
            Short="This is the first Biography entry.",
            Full="This is the first longer entry in the Biographies.",
            Created=get_datetime(),
        )
        db.session.add(entry1)
        db.session.add(entry2)
        db.session.add(entry3)
        db.session.commit()

    def tearDown(self):
        """Clean up the test data we entered."""

    def test_getting_biography_gets_newest(self):
        """When you use GET /biography, it should always return the newest entry in the
        database."""
        response = self.app.get("/api/1.0/biography/")

        self.assertEquals(200, response.status_code)
