import json
import unittest

from sqlalchemy import asc

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
        self.valid_cats = []
        self.valid_cats.append(cats.ReleaseCategoryID)

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
            ReleaseSongDuration=66,
        )
        release_map2 = ReleasesSongsMapping(
            ReleaseID=release.ReleaseID,
            SongID=song2.SongID,
            ReleaseSongDuration=120,
        )
        release_map3 = ReleasesSongsMapping(
            ReleaseID=release.ReleaseID,
            SongID=song3.SongID,
            ReleaseSongDuration=123,
        )
        # It's fine to have the same songs in another release too (could be a live album)
        release2_map1 = ReleasesSongsMapping(
            ReleaseID=release2.ReleaseID,
            SongID=song1.SongID,
            ReleaseSongDuration=66,
        )
        release2_map2 = ReleasesSongsMapping(
            ReleaseID=release2.ReleaseID,
            SongID=song2.SongID,
            ReleaseSongDuration=120,
        )
        release2_map3 = ReleasesSongsMapping(
            ReleaseID=release2.ReleaseID,
            SongID=song3.SongID,
            ReleaseSongDuration=123,
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

    def test_adding_a_release(self):
        """Should insert the release and all it's related data."""
        response = self.app.post(
            "/api/1.0/releases/",
            data=json.dumps(
                dict(
                    title="UnitTest Title",
                    releaseDate=get_datetime(),
                    artist="UnitTest Artist",
                    credits="UnitTest Credits",
                    categories=["UnitTest Category"],
                    formats=["UnitTest Format"],
                    people=[{"UnitTest Person": "UnitTest Guitar"}],
                    songs=[{"UnitTest Song 1": 85}],
                )
            ),
            content_type="application/json"
        )

        release = Releases.query.filter_by(Title="UnitTest Title").first_or_404()

        cats = ReleasesCategoriesMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesCategoriesMapping.ReleaseCategoryID)).all()
        formats = ReleasesFormatsMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesFormatsMapping.ReleaseFormatID)).all()
        people = ReleasesPeopleMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesPeopleMapping.ReleasesPeopleMappingID)).all()
        songs = ReleasesSongsMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesSongsMapping.ReleasesSongsMappingID)).all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest Title", release.Title)
        # These are tested more thoroughly in their own unit tests, so just a simple check here
        self.assertEquals(1, len(cats))
        self.assertEquals(
            "UnitTest Category",
            ReleaseCategories.query.filter_by(
                ReleaseCategoryID=cats[0].ReleaseCategoryID
            ).first().ReleaseCategory
        )
        self.assertEquals(1, len(formats))
        self.assertEquals(
            "UnitTest Format",
            ReleaseFormats.query.filter_by(
                ReleaseFormatID=formats[0].ReleaseFormatID
            ).first().Title
        )
        self.assertEquals(1, len(people))
        self.assertEquals(
            "UnitTest Person",
            People.query.filter_by(PersonID=people[0].PersonID).first().Name
        )
        self.assertEquals(1, len(songs))
        self.assertEquals(
            "UnitTest Song 1",
            Songs.query.filter_by(SongID=songs[0].SongID).first().Title
        )

    def test_updating_release(self):
        """Using PUT will replace the entire release dataset with the new values defined in the
        JSON of the request. All previous values and mapping should be cleared and only the new
        ones will remain."""
        response = self.app.put(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                dict(
                    title="UnitTest Title Put",
                    releaseDate=get_datetime(),
                    artist="UnitTest Artist Put",
                    credits="UnitTest Credits Put",
                    categories=["UnitTest Category Put"],
                    formats=["UnitTest Format Put"],
                    people=[{"UnitTest Person": "UnitTest Guitar Put"}],
                    songs=[{"UnitTest Song 1": 89}],
                )
            ),
            content_type="application/json"
        )

        release = Releases.query.get_or_404(self.release_ids[0])

        cats = ReleasesCategoriesMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesCategoriesMapping.ReleaseCategoryID)).all()
        formats = ReleasesFormatsMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesFormatsMapping.ReleaseFormatID)).all()
        people = ReleasesPeopleMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesPeopleMapping.ReleasesPeopleMappingID)).all()
        songs = ReleasesSongsMapping.query.filter_by(ReleaseID=release.ReleaseID).order_by(
            asc(ReleasesSongsMapping.ReleasesSongsMappingID)).all()

        self.assertEquals(200, response.status_code)
        self.assertEquals("UnitTest Title Put", release.Title)
        self.assertEquals("UnitTest Artist Put", release.Artist)

        # Categories
        self.assertEquals(1, len(cats))
        self.assertEquals(
            "UnitTest Category Put",
            ReleaseCategories.query.filter_by(
                ReleaseCategoryID=cats[0].ReleaseCategoryID
            ).first().ReleaseCategory
        )

        # Formats
        self.assertEquals(1, len(formats))
        self.assertEquals(
            "UnitTest Format Put",
            ReleaseFormats.query.filter_by(
                ReleaseFormatID=formats[0].ReleaseFormatID
            ).first().Title
        )

        # People
        # NB: Any person created during the initial adding of release will still remain. However,
        # the new value in a PUT will be evaluated as usual as either existing, new or invalid.
        # The original person will not be deleted by a PUT, but the mapping for this release will
        # be cleared and replaced with the new people defined in the JSON.
        self.assertEquals(1, len(people))
        self.assertEquals(
            "UnitTest Guitar Put",
            ReleasesPeopleMapping.query.filter_by(
                ReleasesPeopleMappingID=people[0].ReleasesPeopleMappingID
            ).first().Instruments
        )

        # Songs
        # NB: One limitation is that if a Song was first inserted during adding a release and
        # the original had a wrong song duration, then you can only update it for the release
        # mapping. The original song will still have the wrong duration, and we shouldn't update it
        # every time a release is updated, because the time should be release-specific.
        # So the only choice is to use the PUT /songs/:id or PATCH /songs/:id endpoint to update
        # the original song. Or just fix it manually in the DB :)
        self.assertEquals(1, len(songs))
        self.assertEquals(
            89,
            ReleasesSongsMapping.query.filter_by(
                ReleasesSongsMappingID=songs[0].ReleasesSongsMappingID
            ).first().ReleaseSongDuration
        )
