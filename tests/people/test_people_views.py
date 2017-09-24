"""This implements the endpoints used for People specific things."""

import json
import unittest

from app import app, db
from apps.people.models import People, ReleasesPeopleMapping
from apps.releases.models import Releases
from apps.shows.models import Shows, ShowsPeopleMapping
from apps.utils.time import get_datetime


class TestPeopleViews(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        person1 = People(
            Name="UnitTest Person 1"
        )
        person2 = People(
            Name="UnitTest Person 2"
        )
        db.session.add(person1)
        db.session.add(person2)
        db.session.commit()

        self.person1_id = person1.PersonID
        self.person2_id = person2.PersonID

        # Attach the people to Releases. Due to FK, we need a valid ReleaseID
        release = Releases(
            Title="UnitTest Release",
            Date=get_datetime(),
            Artist="UnitTest Artist",
            Credits="UnitTest Credits",
            Created=get_datetime(),
        )
        db.session.add(release)
        db.session.commit()
        self.release_id = release.ReleaseID

        release_person1 = ReleasesPeopleMapping(
            ReleaseID=self.release_id,
            PersonID=person1.PersonID,
            Instruments="UnitTest Drums"
        )
        release_person2 = ReleasesPeopleMapping(
            ReleaseID=self.release_id,
            PersonID=person2.PersonID,
            Instruments="UnitTest Bass"
        )
        db.session.add(release_person1)
        db.session.add(release_person2)
        db.session.commit()

        # Attach them to Shows
        show = Shows(
            ShowDate=get_datetime(),
            CountryCode="UT",
            Country="UnitTest Country",
            City="UnitTest City",
            Venue="UnitTestes"
        )
        db.session.add(show)
        db.session.commit()
        self.show_id = show.ShowID

        show_person1 = ShowsPeopleMapping(
            ShowID=self.show_id,
            PersonID=person1.PersonID,
            Instruments="UnitTest Synths"
        )
        show_person2 = ShowsPeopleMapping(
            ShowID=self.show_id,
            PersonID=person2.PersonID,
            Instruments="UnitTest Cello"
        )
        db.session.add(show_person1)
        db.session.add(show_person2)
        db.session.commit()

    def tearDown(self):
        for person in People.query.filter(People.Name.like("UnitTest%")).all():
            db.session.delete(person)

        r = Releases.query.filter_by(ReleaseID=self.release_id).first()
        db.session.delete(r)

        for rp in ReleasesPeopleMapping.query.filter(
            ReleasesPeopleMapping.Instruments.like("UnitTest%")
        ).all():
            db.session.delete(rp)

        s = Shows.query.filter_by(ShowID=self.show_id).first()
        db.session.delete(s)

        for sp in ShowsPeopleMapping.query.filter(
            ShowsPeopleMapping.Instruments.like("UnitTest%")
        ).all():
            db.session.delete(sp)

        db.session.commit()

    def test_getting_all_people(self):
        """Return all People and the related details, like which releases and shows they appeared
        in and which instruments they used."""
        response = self.app.get("/api/1.0/people/")
        data = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len(data["people"]))

        self.assertEquals("UnitTest Person 1", data["people"][0]["name"])
        self.assertEquals(self.release_id, data["people"][0]["releases"][0]["releaseID"])
        self.assertEquals("UnitTest Drums", data["people"][0]["releases"][0]["instruments"])
        self.assertEquals(self.show_id, data["people"][0]["shows"][0]["showID"])
        self.assertEquals("UnitTest Synths", data["people"][0]["shows"][0]["instruments"])

        self.assertEquals("UnitTest Person 2", data["people"][1]["name"])
        self.assertEquals(self.release_id, data["people"][1]["releases"][0]["releaseID"])
        self.assertEquals("UnitTest Bass", data["people"][1]["releases"][0]["instruments"])
        self.assertEquals(self.show_id, data["people"][1]["shows"][0]["showID"])
        self.assertEquals("UnitTest Cello", data["people"][1]["shows"][0]["instruments"])

    def test_getting_one_person(self):
        """Same as all people, but returns the data of only one person."""
        response = self.app.get("/api/1.0/people/{}".format(self.person1_id))
        data = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(data["people"]))

        self.assertEquals("UnitTest Person 1", data["people"][0]["name"])
        self.assertEquals(self.release_id, data["people"][0]["releases"][0]["releaseID"])
        self.assertEquals("UnitTest Drums", data["people"][0]["releases"][0]["instruments"])
        self.assertEquals(self.show_id, data["people"][0]["shows"][0]["showID"])
        self.assertEquals("UnitTest Synths", data["people"][0]["shows"][0]["instruments"])

    def test_adding_a_person(self):
        """Adding a new person is very straightforward - just a name :)"""
        response = self.app.post(
            "/api/1.0/people/",
            data=json.dumps(
                dict(
                    name="UnitTest Added"
                )
            ),
            content_type="application/json"
        )

        person = People.query.filter_by(Name="UnitTest Added").first_or_404()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.data.decode())
        self.assertNotEquals(None, person)
        self.assertEquals("UnitTest Added", person.Name)

    def test_updating_a_person(self):
        """Equally easy as adding one. Since a Person only has one column, we use just PUT and do
        not implement PATCH."""
        response = self.app.put(
            "/api/1.0/people/{}".format(self.person2_id),
            data=json.dumps(
                dict(
                    name="UnitTest Updated"
                )
            ),
            content_type="application/json"
        )

        person = People.query.filter_by(PersonID=self.person2_id).first_or_404()

        self.assertEquals(200, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertNotEquals(None, person)
        self.assertEquals("UnitTest Updated", person.Name)

    def test_deleting_a_person(self):
        """Not much to it."""
        response = self.app.delete("/api/1.0/people/{}".format(self.person1_id))

        person = People.query.filter_by(PersonID=self.person1_id).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals(None, person)
