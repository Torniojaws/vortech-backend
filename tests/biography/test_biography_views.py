import json
import unittest

from flask_caching import Cache
from sqlalchemy import desc, or_

from app import app, db
from apps.biography.models import Biography
from apps.utils.time import get_datetime


class TestBiographyViews(unittest.TestCase):
    def setUp(self):
        """Add some test entries to the database, so we can test getting the latest one."""

        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        entry1 = Biography(
            Short="UnitTest This is the first Biography entry.",
            Full="This is the first longer entry in the Biographies.",
            Created=get_datetime(),
        )
        entry2 = Biography(
            Short="UnitTest This is the second Biography entry.",
            Full="This is the second longer entry in the Biographies.",
            Created=get_datetime(),
        )
        entry3 = Biography(
            Short="UnitTest This is the third Biography entry.",
            Full="This is the third longer entry in the Biographies.",
            Created=get_datetime(),
        )
        db.session.add(entry1)
        db.session.add(entry2)
        db.session.add(entry3)
        db.session.commit()

    def tearDown(self):
        """Clean up the test data we entered."""
        to_delete = Biography.query.filter(
            or_(
                Biography.Short.like("UnitTest%"),
                Biography.Full.like("This is the third%")
            )
        ).all()
        for bio in to_delete:
            db.session.delete(bio)
        db.session.commit()

    def test_getting_biography_gets_newest(self):
        """When you use GET /biography, it should always return the newest entry in the
        database."""
        response = self.app.get("/api/1.0/biography/")

        self.assertEquals(200, response.status_code)
        self.assertTrue("third" in response.get_data().decode())

    def test_adding_biography(self):
        """Should add a new entry to the table and then GET should return it."""
        response = self.app.post(
            "/api/1.0/biography/",
            data=json.dumps(
                dict(
                    short="UnitTest fourth short",
                    full="UnitTest fourth full",
                )
            ),
            content_type="application/json"
        )
        bio = Biography.query.filter(Biography.Short.like("%fourth%")).first()

        get_bio = self.app.get("/api/1.0/biography/")
        biodata = json.loads(get_bio.get_data().decode())

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest fourth short", bio.Short)
        self.assertEquals("UnitTest fourth full", bio.Full)

        # Verify the result of GET after the POST
        self.assertEquals(200, get_bio.status_code)
        self.assertEquals("UnitTest fourth full", biodata["biography"][0]["full"])

    def test_updating_biography(self):
        """Should update the current newest entry with the data in the JSON."""
        response = self.app.put(
            "/api/1.0/biography/",
            data=json.dumps(
                dict(
                    short="UnitTest Updated newest short",
                    full="UnitTest Updated newest full",
                )
            ),
            content_type="application/json"
        )

        get_bio = self.app.get("/api/1.0/biography/")
        biodata = json.loads(get_bio.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(200, get_bio.status_code)
        self.assertEquals("UnitTest Updated newest short", biodata["biography"][0]["short"])
        self.assertEquals("UnitTest Updated newest full", biodata["biography"][0]["full"])

    def test_patching_biography_using_add(self):
        """Should update only one of the two columns in the newest biography, and should update
        the Updated datetime of it. Since it doesn't really make sense to append to a one row only
        item like biography is, "add" will behave like replace. It could be left unimplemented too
        I guess."""
        response = self.app.patch(
            "/api/1.0/biography/",
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/short",
                        value="UnitTest Patched Short",
                    ),
                    dict(
                        op="add",
                        path="/full",
                        value="UnitTest Patched Full",
                    ),
                ]
            ),
            content_type="application/json"
        )

        current_bio = Biography.query.order_by(desc(Biography.BiographyID)).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest Patched Short", current_bio.Short)
        self.assertEquals("UnitTest Patched Full", current_bio.Full)

    def test_patching_biography_using_copy(self):
        """Copy a resource to target location."""
        response = self.app.patch(
            "/api/1.0/biography/",
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/full",
                        "path": "/short",
                    })
                ]
            ),
            content_type="application/json"
        )

        current_bio = Biography.query.order_by(desc(Biography.BiographyID)).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("This is the third longer entry in the Biographies.", current_bio.Short)

    def test_patching_biography_using_move(self):
        """Move a resource to target location and delete source. But in Biography, there are no
        nullable columns, so move cannot be used. Thus a 422 Unprocessable Entity is returned."""
        response = self.app.patch(
            "/api/1.0/biography/",
            data=json.dumps(
                [
                    dict({
                        "op": "move",
                        "from": "/short",
                        "path": "/full",
                    }),
                ]
            ),
            content_type="application/json"
        )

        current_bio = Biography.query.order_by(desc(Biography.BiographyID)).first()

        self.assertEquals(422, response.status_code)
        # Make sure nothing changed.
        self.assertEquals("This is the third longer entry in the Biographies.", current_bio.Full)

    def test_patching_biography_using_remove(self):
        """Remove a resource. But, because both of the resources in Biography are nullable=False,
        they cannot be removed in the database. So we should return a 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/biography/",
            data=json.dumps(
                [
                    dict({
                        "op": "remove",
                        "path": "/full",
                    }),
                ]
            ),
            content_type="application/json"
        )

        current_bio = Biography.query.order_by(desc(Biography.BiographyID)).first()

        self.assertEquals(422, response.status_code)
        # Make sure it was not removed. Although it is NOT NULL...
        self.assertEquals("This is the third longer entry in the Biographies.", current_bio.Full)

    def test_patching_biography_using_replace(self):
        """Replace the contents of a resource with a new value."""
        response = self.app.patch(
            "/api/1.0/biography/",
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/full",
                        "value": "UnitTest patched with replace"
                    }),
                ]
            ),
            content_type="application/json"
        )

        current_bio = Biography.query.order_by(desc(Biography.BiographyID)).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest patched with replace", current_bio.Full)

    # "op": "test" will be implemented later
