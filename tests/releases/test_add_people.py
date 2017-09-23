"""CFPS = Categories, Formats, People, Songs. They are quite complex, so they were implemented
separately for the POST /releases handling. Note that ALL of the functions here insert things into
their "standalone" tables. We also test the mapping."""

import unittest

from sqlalchemy import asc

from app import db
from apps.people.models import People, ReleasesPeopleMapping
from apps.releases.add_cfps import add_people
from apps.releases.models import Releases
from apps.utils.time import get_datetime


class TestAddPeople(unittest.TestCase):
    def setUp(self):
        # The release we use for these tests
        release = Releases(
            Title="UnitTest",
            Date=get_datetime(),
            Artist="UnitTest Arts",
            Credits="UnitTest is a good and fun activity",
            Created=get_datetime(),
        )
        db.session.add(release)
        db.session.commit()
        self.release_id = release.ReleaseID

        # For testing an existing person
        person = People(
            Name="UnitTest Super Guitar"
        )
        db.session.add(person)
        db.session.commit()
        self.existing_person_id = person.PersonID

    def tearDown(self):
        people = People.query.filter(
            People.Name.like("UnitTest%")
        ).all()
        for person in people:
            db.session.delete(person)
        db.session.commit()

        release = Releases.query.filter_by(ReleaseID=self.release_id).first()
        db.session.delete(release)
        db.session.commit()

    def test_adding_people_by_existing_id(self):
        """When an integer is used, it presumably refers to an existing person in the People table.
        So we check does the person ID exist. If it does, we'll map the release to that ID.
        Otherwise we ignore the mapping, since it is an invalid ID."""
        person_dict = {self.existing_person_id: "UnitTest Drums"}
        add_people(self.release_id, [person_dict])

        people = People.query.all()
        mapping = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(people))
        self.assertEquals(1, len(mapping))
        self.assertEquals(self.existing_person_id, mapping[0].PersonID)
        self.assertEquals("UnitTest Drums", mapping[0].Instruments)

    def test_adding_people_with_new_string_values(self):
        """Should create new entries and then do the mapping for the current release."""
        person1 = {"UnitTest Mike": "Drums"}
        person2 = {"UnitTest John": "Guitar"}
        people = [person1, person2]
        add_people(self.release_id, people)

        people = People.query.all()
        mapping = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_id).order_by(
            asc(ReleasesPeopleMapping.ReleasesPeopleMappingID)
        ).all()

        # Should be connected to the release
        p1 = People.query.filter_by(Name="UnitTest Mike").first()
        p2 = People.query.filter_by(Name="UnitTest John").first()

        self.assertEquals(3, len(people))
        self.assertFalse(p1 is None)
        self.assertFalse(p2 is None)
        self.assertEquals(mapping[0].PersonID, p1.PersonID)
        self.assertEquals(mapping[0].Instruments, "Drums")
        self.assertEquals(mapping[1].PersonID, p2.PersonID)
        self.assertEquals(mapping[1].Instruments, "Guitar")

    def test_adding_people_with_existing_string_values(self):
        """Should not add a new entry to People, and the mapping should be correct for current
        release.

        Note that there shouldn't be multiple mappings for one person playing multiple instruments
        on a release. The idea is to describe multiple instruments with a string like:
        "Guitar and drums", since we don't really need further granularity."""
        people_list = [{"UnitTest Super Guitar": "Guitar"}]
        add_people(self.release_id, people_list)

        people = People.query.all()
        mapping = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(people))
        self.assertEquals(people[0].PersonID, mapping[0].PersonID)
        self.assertEquals("Guitar", mapping[0].Instruments)

    def test_adding_people_with_nonexisting_ids(self):
        """When you add PersonIDs that do not exist, no mapping should happen and no new entries
        should appear in ReleasesPeopleMapping."""
        add_people(self.release_id, [{0: "Yappety"}])

        people = People.query.all()
        mapping = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_id).first()

        self.assertEquals(1, len(people))
        self.assertTrue(mapping is None)
