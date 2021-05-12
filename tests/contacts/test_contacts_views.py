"""Contacts are quite simple. It contains some links to tech riders and contact information in a
single database row. They basically could be hard-coded to the site too, but for some flexibility
they'll be in the DB."""

import json
import unittest

from flask_caching import Cache
from sqlalchemy import desc

from app import app, db
from apps.contacts.models import Contacts
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime_one_hour_ahead


class TestContactsViews(unittest.TestCase):
    def setUp(self):

        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "RedisCache"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Insert two contacts entries to test we get the newest by Created
        c1 = Contacts(
            Email="unittest@email.com",
            TechRider="unittest-techrider2016.pdf",
            InputList="unittest-inputlist2016.pdf",
            Backline="unittest-backline2016.pdf",
            Created="2017-01-01 10:00:00",
        )
        c2 = Contacts(
            Email="unittest@email.com",
            TechRider="unittest-techrider.pdf",
            InputList="unittest-inputlist.pdf",
            Backline="unittest-backline.pdf",
            Created="2017-03-04 05:06:07",
        )
        db.session.add(c1)
        db.session.add(c2)
        db.session.commit()

        # We also need a valid admin user for the add release endpoint test.
        user = Users(
            Name="UnitTest Admin",
            Username="unittest",
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
        for contact in Contacts.query.filter(Contacts.Email.like("unittest%")).all():
            db.session.delete(contact)
        db.session.commit()

        user = Users.query.filter_by(UserID=self.user_id).first()
        db.session.delete(user)
        db.session.commit()

    def test_getting_contacts_is_latest(self):
        """When you GET /contacts, it should return the newest contact information."""
        response = self.app.get("/api/1.0/contacts/")
        data = json.loads(response.data.decode())

        newest = Contacts.query.order_by(
            desc(Contacts.Created)
        ).first_or_404()

        self.assertEqual(200, response.status_code)
        self.assertEqual(newest.ContactsID, data["contacts"][0]["id"])
        self.assertEqual("unittest@email.com", data["contacts"][0]["email"])
        self.assertEqual("unittest-techrider.pdf", data["contacts"][0]["techRider"])
        self.assertEqual("unittest-inputlist.pdf", data["contacts"][0]["inputList"])
        self.assertEqual("unittest-backline.pdf", data["contacts"][0]["backline"])
        self.assertNotEqual(0, len(data["contacts"][0]["createdAt"]))

    def test_adding_a_contacts_entry(self):
        """When a new Contacts entry is added, it should be returned instead of the previous
        Contacts entry when doing a GET /contacts."""
        response = self.app.post(
            "/api/1.0/contacts/",
            data=json.dumps(
                dict(
                    email="unittest-post@email.com",
                    techRider="unittest-post-techrider.pdf",
                    inputList="unittest-post-inputlist.pdf",
                    backline="unittest-post-backline.pdf",
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        get_contacts = self.app.get("/api/1.0/contacts/")
        data = json.loads(get_contacts.data.decode())

        newest = Contacts.query.order_by(
            desc(Contacts.Created)
        ).first_or_404()

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in response.data.decode())

        self.assertEqual(200, get_contacts.status_code)
        self.assertEqual(newest.ContactsID, data["contacts"][0]["id"])
        self.assertEqual("unittest-post@email.com", data["contacts"][0]["email"])
        self.assertEqual("unittest-post-techrider.pdf", data["contacts"][0]["techRider"])
        self.assertEqual("unittest-post-inputlist.pdf", data["contacts"][0]["inputList"])
        self.assertEqual("unittest-post-backline.pdf", data["contacts"][0]["backline"])
        self.assertNotEqual(0, len(data["contacts"][0]["createdAt"]))

    def test_patching_contacts_using_add(self):
        """Partially update a value in the newest contact entry."""
        response = self.app.patch(
            "/api/1.0/contacts/",
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/email",
                        value="unittest-patched@email.com",
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        newest = Contacts.query.order_by(
            desc(Contacts.Created)
        ).first_or_404()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", response.data.decode())
        self.assertEqual("unittest-patched@email.com", newest.Email)

    def test_patching_contacts_using_copy(self):
        """Copy a value in the newest contact entry from one resource to another."""
        response = self.app.patch(
            "/api/1.0/contacts/",
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/inputList",
                        "path": "/techRider",
                    }),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        newest = Contacts.query.order_by(
            desc(Contacts.Created)
        ).first_or_404()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", response.data.decode())
        self.assertEqual("unittest-inputlist.pdf", newest.TechRider)
        self.assertEqual("unittest-inputlist.pdf", newest.InputList)

    # TODO: Move, Remove and Test will be implemented later

    def test_patching_contacts_using_replace(self):
        """Replace a value in the newest contact entry with a new value."""
        response = self.app.patch(
            "/api/1.0/contacts/",
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/backline",
                        "value": "unittest-patched-backline.pdf"
                    }),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        newest = Contacts.query.order_by(
            desc(Contacts.Created)
        ).first_or_404()

        self.assertEqual(204, response.status_code)
        self.assertEqual("", response.data.decode())
        self.assertEqual("unittest-patched-backline.pdf", newest.Backline)

    def test_patching_with_exception(self):
        """Test a patch that results in 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/contacts/",
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

        self.assertEqual(422, response.status_code)
        self.assertFalse("", response.data.decode())
