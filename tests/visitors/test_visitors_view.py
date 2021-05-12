"""The visitors view is very simple, as you can only do a GET to retrieve the count and obviously
POST to add to the count."""

import json
import unittest

from datetime import datetime
from sqlalchemy import desc

from app import app, db
from apps.utils.time import get_datetime, get_date, get_monday, get_first_day
from apps.visitors.models import Visitors


class TestVisitorsViews(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        # We need 3 entries for "today" (country and continent will come from geolite2)
        # NB: Because this would get complex in unit testing, we simply pick a date as a reference
        # point for "today" that we then use as a basis for what is "this week" and "this month",
        # purely for testing purposes.
        today1 = Visitors(
            IPAddress="127.0.0.1",
            VisitDate=get_datetime(),
            Continent="Europe",
            Country="Finland",
        )
        today2 = Visitors(
            IPAddress="127.0.0.1",
            VisitDate=get_datetime(),
            Continent="Europe",
            Country="Sweden",
        )
        today3 = Visitors(
            IPAddress="127.0.0.1",
            VisitDate=get_datetime(),
            Continent="Europe",
            Country="Norway",
        )
        db.session.add(today1)
        db.session.add(today2)
        db.session.add(today3)
        db.session.commit()

        # ...and 2 more entries for "this week". This is kind of hairy on a Monday.
        week1 = Visitors(
            IPAddress="127.0.0.1",
            VisitDate=get_monday(),
            Continent="Europe",
            Country="Finland",
        )
        week2 = Visitors(
            IPAddress="127.0.0.1",
            VisitDate=get_monday(),
            Continent="Europe",
            Country="Sweden",
        )
        db.session.add(week1)
        db.session.add(week2)
        db.session.commit()

        # ...and another 2 entries for "this month"
        month1 = Visitors(
            IPAddress="127.0.0.1",
            VisitDate=get_first_day(),
            Continent="Europe",
            Country="Finland",
        )
        month2 = Visitors(
            IPAddress="127.0.0.1",
            VisitDate=get_first_day(),
            Continent="Europe",
            Country="Sweden",
        )
        db.session.add(month1)
        db.session.add(month2)
        db.session.commit()

    def tearDown(self):
        for visit in Visitors.query.filter_by(IPAddress="127.0.0.1").all():
            db.session.delete(visit)
        db.session.commit()

        # Special real IP test
        Visitors.query.filter_by(Country="Republic of Lithuania").delete()
        db.session.commit()

    def test_getting_visitor_count(self):
        """The visitor count should return the total count and counts by current day/week/month."""
        response = self.app.get("/api/1.0/visits/")
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertTrue("month" in data["visits"])
        self.assertTrue("week" in data["visits"])
        self.assertTrue("today" in data["visits"])

        all_integers = False
        try:
            int(data["visits"]["month"])
            int(data["visits"]["week"])
            int(data["visits"]["today"])
            all_integers = True
        except ValueError:
            all_integers = False
        self.assertTrue(all_integers)

    def test_incrementing_visits_in_localhost(self):
        """When we POST a valid JSON, we should also get our geodata and add it to the table."""
        response = self.app.post(
            "/api/1.0/visits/",
            data=json.dumps(
                dict({
                    "increment": 1
                })
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        visit = Visitors.query.order_by(desc(Visitors.VisitID)).first()
        count = Visitors.query.filter(Visitors.VisitDate >= get_date()).all()

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in data)

        self.assertEqual("Unknown", visit.Country)  # You cannot get valid data in localhost

        if datetime.now().weekday() == 0 or datetime.now().day == 1:
            # When run on a Monday or the 1st day of the month
            self.assertEqual(6, len(count))
        else:
            self.assertEqual(4, len(count))

    def test_incrementing_visits_with_mocked_IP(self):
        """When we POST a valid JSON, we should also get our geodata and add it to the table."""
        response = self.app.post(
            "/api/1.0/visits/",
            data=json.dumps(
                dict({
                    "increment": 1
                })
            ),
            content_type="application/json",
            environ_base={'REMOTE_ADDR': '212.24.107.55'}  # This is the IP of the VPS we host in
        )
        data = json.loads(response.data.decode())

        visit = Visitors.query.order_by(desc(Visitors.VisitID)).first()
        count = Visitors.query.filter(Visitors.VisitDate >= get_date()).all()

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in data)

        self.assertEqual("Europe", visit.Continent)
        self.assertEqual("Republic of Lithuania", visit.Country)

        if datetime.now().weekday() == 0 or datetime.now().day == 1:
            # When run on a Monday or the 1st day of the month
            self.assertEqual(6, len(count))
        else:
            self.assertEqual(4, len(count))

    def test_incrementing_visits_with_invalid_json(self):
        """When we POST an invalid JSON, the request should be ignored and we get an error JSON."""
        response = self.app.post(
            "/api/1.0/visits/",
            data=json.dumps(
                dict({
                    "nope": "Heyy"
                })
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        visit = Visitors.query.order_by(desc(Visitors.VisitID)).first()
        count = Visitors.query.filter(Visitors.VisitDate >= get_date()).all()

        self.assertEqual(400, response.status_code)
        self.assertNotEqual(None, data)
        self.assertEqual("Invalid data in visitor counter update", data["error"])
        self.assertFalse(data["success"])

        self.assertEqual("Europe", visit.Continent)

        if datetime.now().weekday() == 0 or datetime.now().day == 1:
            # When run on a Monday or 1st day of the month
            self.assertEqual(5, len(count))
        else:
            self.assertEqual(3, len(count))
