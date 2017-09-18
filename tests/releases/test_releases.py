import json
import unittest

from app import app, db
from apps.releases.models import (
    Releases,
    ReleaseFormats,
    ReleasesFormatsMapping,
    ReleaseCategories,
    ReleasesCategoriesMapping
)
from apps.people.models import People, ReleasesPeopleMapping
from apps.songs.models import Songs, ReleasesSongsMapping
from apps.utils.time import get_datetime


class TestReleases(unittest.TestCase):
    """Terms used in the tests.
    CFPS:
    C = Categories (Full length, Live, Demo, etc)
    F = Formats (CD, CD-R, Digital, etc)
    P = People (who plays what on the album)
    S = Songs (foreign key IDs)
    """

    def setUp(self):
        self.app = app.test_client()

        # Add two test releases
        release = Releases(
            Title="UnitTest",
            Date=get_datetime(),
            Artist="UnitTest Arts",
            Credits="UnitTest is a good and fun activity",
            Created=get_datetime(),
        )
        release2 = Releases(
            Title="UnitTest 2",
            Date=get_datetime(),
            Artist="UnitTest 2 Arts",
            Credits="UnitTest too is good for testing",
            Created=get_datetime(),
        )
        db.session.add(release)
        db.session.add(release2)
        # Flush, so we can use the insert ID below
        db.session.flush()
        self.release_ids = []
        self.release_ids.append(release.ReleaseID)
        self.release_ids.append(release2.ReleaseID)

        # Add categories and mapping for the releases
        cats = ReleaseCategories(
            ReleaseCategory="UnitTest Category"
        )
        db.session.add(cats)
        db.session.flush()

        cat_map = ReleasesCategoriesMapping(
            ReleaseID=release.ReleaseID,
            ReleaseCategoryID=cats.ReleaseCategoryID,
        )
        cat_map2 = ReleasesCategoriesMapping(
            ReleaseID=release2.ReleaseID,
            ReleaseCategoryID=cats.ReleaseCategoryID,
        )
        db.session.add(cat_map)
        db.session.add(cat_map2)

        # Add formats and mapping for the release
        format_cd = ReleaseFormats(
            Title="CD"
        )
        format_digital = ReleaseFormats(
            Title="Digital"
        )
        db.session.add(format_cd)
        db.session.add(format_digital)
        db.session.flush()

        format_mapping = ReleasesFormatsMapping(
            ReleaseFormatID=format_cd.ReleaseFormatID,
            ReleaseID=release.ReleaseID,
        )
        format_mapping2 = ReleasesFormatsMapping(
            ReleaseFormatID=format_cd.ReleaseFormatID,
            ReleaseID=release2.ReleaseID,
        )
        db.session.add(format_mapping)
        db.session.add(format_mapping2)

        # Add people and mapping for the release. For some reason, this sometimes is not deleted
        # by tearDown. XXX: Not sure why, so we just check if it exists and use the existing.
        person = People.query.filter_by(Name="UnitTester").first()
        if not person:
            person = People(
                Name="UnitTester"
            )
            db.session.add(person)
            db.session.flush()

        person_map = ReleasesPeopleMapping(
            ReleaseID=release.ReleaseID,
            PersonID=person.PersonID,
            Instruments="UnitTesting with Guitars",
        )
        person_map2 = ReleasesPeopleMapping(
            ReleaseID=release2.ReleaseID,
            PersonID=person.PersonID,
            Instruments="UnitTesting with Extra spice",
        )
        db.session.add(person_map)
        db.session.add(person_map2)

        # Add songs for the release
        song1 = Songs(
            Title="UnitTest One",
            Duration=66,
        )
        song2 = Songs(
            Title="UnitTest Two",
            Duration=120,
        )
        song3 = Songs(
            Title="UnitTest Three",
            Duration=123,
        )
        db.session.add(song1)
        db.session.add(song2)
        db.session.add(song3)
        db.session.flush()

        release_map1 = ReleasesSongsMapping(
            ReleaseID=release.ReleaseID,
            SongID=song1.SongID,
        )
        release_map2 = ReleasesSongsMapping(
            ReleaseID=release.ReleaseID,
            SongID=song2.SongID,
        )
        release_map3 = ReleasesSongsMapping(
            ReleaseID=release.ReleaseID,
            SongID=song3.SongID,
        )
        # It's fine to have the same songs in another release too (could be a live album)
        release2_map1 = ReleasesSongsMapping(
            ReleaseID=release2.ReleaseID,
            SongID=song1.SongID,
        )
        release2_map2 = ReleasesSongsMapping(
            ReleaseID=release2.ReleaseID,
            SongID=song2.SongID,
        )
        release2_map3 = ReleasesSongsMapping(
            ReleaseID=release2.ReleaseID,
            SongID=song3.SongID,
        )

        db.session.add(release_map1)
        db.session.add(release_map2)
        db.session.add(release_map3)

        db.session.add(release2_map1)
        db.session.add(release2_map2)
        db.session.add(release2_map3)

        # Phew! Let's commit
        db.session.commit()

    def tearDown(self):
        # This will delete all the mappings too, via ondelete cascade
        releases = Releases.query.filter(Releases.Title.like("UnitTest%")).all()
        for release in releases:
            db.session.delete(release)
        db.session.commit()

        # But the CFPS need to be deleted separately
        cats = ReleaseCategories.query.filter(
            ReleaseCategories.ReleaseCategory.like("UnitTest%")).all()
        for cat in cats:
            db.session.delete(cat)
        db.session.commit()

        formats = ReleaseFormats.query.all()
        for f in formats:
            db.session.delete(f)
        db.session.commit()

        people = People.query.filter(People.Name.like("UnitTest%")).all()
        for person in people:
            db.session.delete(person)
        db.session.commit()

        songs = Songs.query.filter(Songs.Title.like("UnitTest%")).all()
        for song in songs:
            db.session.delete(song)
        db.session.commit()

    def test_getting_one_release(self):
        """This should return all the details of a single release, including the CFPS"""
        response = self.app.get("/api/1.0/releases/{}".format(self.release_ids[0]))
        release = json.loads(
            response.get_data().decode()
        )

        self.assertEquals(200, response.status_code)
        self.assertFalse(release is None)
        self.assertEquals("UnitTest Arts", release["releases"][0]["artist"])
        self.assertEquals("UnitTest is a good and fun activity", release["releases"][0]["credits"])
        self.assertEquals(1, len(release["releases"][0]["categories"]))
        self.assertEquals(1, len(release["releases"][0]["formats"]))
        self.assertEquals(1, len(release["releases"][0]["people"]))
        self.assertEquals(3, len(release["releases"][0]["songs"]))

    def test_getting_all_releases(self):
        """Should return all the releases and all their details, including CFPS, in reverse
        chronological order (newest release first)"""
        response = self.app.get("/api/1.0/releases/")
        releases = json.loads(
            response.get_data().decode()
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len(releases["releases"]))
        self.assertEquals("UnitTest 2", releases["releases"][0]["title"])
        self.assertEquals("UnitTest", releases["releases"][1]["title"])
        self.assertEquals(1, len(releases["releases"][0]["categories"]))
        self.assertEquals(1, len(releases["releases"][0]["formats"]))
        self.assertEquals(1, len(releases["releases"][0]["people"]))
        self.assertEquals(3, len(releases["releases"][0]["songs"]))
        self.assertEquals(1, len(releases["releases"][1]["categories"]))
        self.assertEquals(1, len(releases["releases"][1]["formats"]))
        self.assertEquals(1, len(releases["releases"][1]["people"]))
        self.assertEquals(3, len(releases["releases"][1]["songs"]))
