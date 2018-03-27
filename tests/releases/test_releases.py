import json
import unittest

from flask_caching import Cache
from sqlalchemy import asc

from app import app, db
from apps.releases.models import (
    Releases,
    ReleaseFormats,
    ReleasesFormatsMapping,
    ReleaseCategories,
    ReleasesCategoriesMapping
)
from apps.releases.patches import patch_mapping
from apps.people.models import People, ReleasesPeopleMapping
from apps.songs.models import Songs, ReleasesSongsMapping
from apps.users.models import Users, UsersAccessTokens, UsersAccessMapping, UsersAccessLevels
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestReleases(unittest.TestCase):
    """Terms used in the tests.
    CFPS:
    C = Categories (Full length, Live, Demo, etc)
    F = Formats (CD, CD-R, Digital, etc)
    P = People (who plays what on the album)
    S = Songs (foreign key IDs)
    """

    def setUp(self):
        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Add two test releases
        release = Releases(
            Title="UnitTest",
            Date=get_datetime(),
            Artist="UnitTest Arts",
            Credits="UnitTest is a good and fun activity",
            Created=get_datetime(),
            ReleaseCode="TEST001"
        )
        release2 = Releases(
            Title="UnitTest 2",
            Date=get_datetime(),
            Artist="UnitTest 2 Arts",
            Credits="UnitTest too is good for testing",
            Created=get_datetime(),
            ReleaseCode="TEST002"
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
        cats2 = ReleaseCategories(
            ReleaseCategory="UnitTest Category 2"
        )
        cats3 = ReleaseCategories(
            ReleaseCategory="UnitTest Category 3"
        )
        db.session.add(cats)
        db.session.add(cats2)
        db.session.add(cats3)
        db.session.flush()
        self.valid_cats = []
        self.valid_cats.append(cats.ReleaseCategoryID)
        self.valid_cats.append(cats2.ReleaseCategoryID)
        self.valid_cats.append(cats3.ReleaseCategoryID)

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

        # For patch testing
        format1 = ReleaseFormats(
            Title="UnitTest Format One"
        )
        format2 = ReleaseFormats(
            Title="UnitTest Format Two"
        )
        db.session.add(format1)
        db.session.add(format2)
        db.session.flush()
        self.valid_formats = []
        self.valid_formats.append(format1.ReleaseFormatID)
        self.valid_formats.append(format2.ReleaseFormatID)

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

        # For testing patching:
        person1 = People(
            Name="UnitTest Person One"
        )
        person2 = People(
            Name="UnitTest Person Two"
        )
        db.session.add(person1)
        db.session.add(person2)
        db.session.flush()
        self.valid_people = []
        self.valid_people.append(person1.PersonID)
        self.valid_people.append(person2.PersonID)

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
        # And some patch songs
        song_p1 = Songs(
            Title="UnitTest Patch One",
            Duration=59,
        )
        song_p2 = Songs(
            Title="UnitTest Patch Two",
            Duration=161,
        )
        db.session.add(song1)
        db.session.add(song2)
        db.session.add(song3)
        db.session.add(song_p1)
        db.session.add(song_p2)
        db.session.flush()
        self.valid_songs = []
        self.valid_songs.append(song_p1.SongID)
        self.valid_songs.append(song_p2.SongID)

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

        user = Users.query.filter_by(UserID=self.user_id).first()
        db.session.delete(user)
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
        # SongID is used for lyrics and tabs
        self.assertTrue("id" in release["releases"][0]["songs"][0])
        self.assertTrue(type(int(release["releases"][0]["songs"][0]["id"])) == int)

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
        # SongID is used for lyrics and tabs
        self.assertTrue("id" in releases["releases"][0]["songs"][0])
        self.assertTrue(type(int(releases["releases"][0]["songs"][0]["id"])) == int)
        self.assertTrue("id" in releases["releases"][1]["songs"][0])
        self.assertTrue(type(int(releases["releases"][1]["songs"][0]["id"])) == int)

    def test_adding_a_release(self):
        """Should insert the release and all it's related data.
        NB: This endpoint requires a valid admin token in the request header. We create one in
        setUp() for this test."""
        response = self.app.post(
            "/api/1.0/releases/",
            data=json.dumps(
                dict(
                    title="UnitTest Title",
                    releaseCode="TEST001",
                    releaseDate=get_datetime(),
                    artist="UnitTest Artist",
                    credits="UnitTest Credits",
                    categories=["UnitTest Category"],
                    formats=["UnitTest Format"],
                    people=[{"UnitTest Person": "UnitTest Guitar"}],
                    songs=[{"UnitTest Song 1": 85}],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
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
                    releaseCode="TEST001",
                    releaseDate=get_datetime(),
                    artist="UnitTest Artist Put",
                    credits="UnitTest Credits Put",
                    categories=["UnitTest Category Put"],
                    formats=["UnitTest Format Put"],
                    people=[{"UnitTest Person": "UnitTest Guitar Put"}],
                    songs=[{"UnitTest Song 1": 89}],
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
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

    def test_patch_mapping(self):
        """Because the JSON values can be in different case than the actual DB model, we map them
        to the correct case."""
        patch = [
            {"op": "add", "path": "/title", "value": "testi"},
            {"op": "copy", "from": "/releaseDate", "path": "/artist"},
            {"op": "remove", "path": "/credits"},
            {"op": "replace", "path": "/categories", "value": [2, 3]},
            {"op": "remove", "path": "/formats"},
            {"op": "copy", "from": "/people", "path": "/songs"},
        ]

        mapped_patchdata = []
        for p in patch:
            p = patch_mapping(p)
            mapped_patchdata.append(p)

        self.assertEquals(6, len(mapped_patchdata))
        self.assertEquals("add", mapped_patchdata[0]["op"])
        self.assertEquals("replace", mapped_patchdata[3]["op"])
        self.assertEquals("/Title", mapped_patchdata[0]["path"])
        self.assertEquals("testi", mapped_patchdata[0]["value"])
        self.assertEquals("/Date", mapped_patchdata[1]["from"])
        self.assertEquals("/Artist", mapped_patchdata[1]["path"])
        self.assertEquals("/Credits", mapped_patchdata[2]["path"])
        self.assertEquals("/Categories", mapped_patchdata[3]["path"])
        self.assertEquals("/Formats", mapped_patchdata[4]["path"])
        self.assertEquals("/People", mapped_patchdata[5]["from"])
        self.assertEquals("/Songs", mapped_patchdata[5]["path"])

    """The below contains the actual implementation of the patching logic for PATCH /endpoint
    requests.  The RFC 6902 definition is used."""

    def test_patching_using_add(self):
        """Add can be used to insert new values into the existing resource."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/title",
                        value="UnitTest Patched Title",
                    ),
                    dict(
                        op="add",
                        path="/artist",
                        value="UnitTest Patched Artist",
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        release = Releases.query.get_or_404(self.release_ids[0])

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest Patched Title", release.Title)
        self.assertEquals("UnitTest Patched Artist", release.Artist)

    def test_patching_using_add_in_categories(self):
        """Add can be used to insert new values into the existing resource."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/categories",
                        value=["UnitTest patched category"],
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        cats = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesCategoriesMapping.ReleaseCategoryID)).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals(2, len(cats))

        self.assertEquals(
            "UnitTest patched category",
            ReleaseCategories.query.filter_by(
                ReleaseCategoryID=cats[1].ReleaseCategoryID
            ).first().ReleaseCategory
        )

    def test_patching_using_add_in_formats(self):
        """Add can be used to insert new values into the existing resource."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/formats",
                        value=["UnitTest patched format"],
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        formats = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesFormatsMapping.ReleaseFormatID)).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals(2, len(formats))
        self.assertEquals(
            "UnitTest patched format",
            ReleaseFormats.query.filter_by(
                ReleaseFormatID=formats[1].ReleaseFormatID
            ).first().Title
        )

    def test_patching_using_add_in_people(self):
        """Add can be used to insert new values into the existing resource."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/people",
                        value=[{"UnitTest patched person": "Synths"}],
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        people = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesPeopleMapping.PersonID)).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals(2, len(people))
        self.assertEquals(
            "UnitTest patched person",
            People.query.filter_by(
                PersonID=people[1].PersonID
            ).first().Name
        )
        self.assertEquals(
            "Synths",
            ReleasesPeopleMapping.query.filter_by(
                PersonID=people[1].PersonID
            ).first().Instruments
        )

    def test_patching_using_add_in_songs(self):
        """Add can be used to insert new values into the existing resource."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/songs",
                        value=[{"UnitTest patched Song 2": 290}],
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        songs = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesSongsMapping.SongID)).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals(4, len(songs))
        self.assertEquals(
            "UnitTest patched Song 2",
            Songs.query.filter_by(
                SongID=songs[3].SongID
            ).first().Title
        )
        self.assertEquals(
            290,
            ReleasesSongsMapping.query.filter_by(
                SongID=songs[3].SongID
            ).first().ReleaseSongDuration
        )

    def test_patching_using_copy(self):
        """Copy is used to copy one resource to another."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[1])),
            data=json.dumps(
                [{
                    "op": "copy",
                    "from": "/artist",  # Cannot use from in a dict. It is a keyword
                    "path": "/title"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        release = Releases.query.get_or_404(self.release_ids[1])

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest 2 Arts", release.Title)

    def test_patching_using_copy_in_categories(self):
        """For Release Categories, the "copy" patch has no meaning, as there is nowhere to copy to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "copy",
                    "from": "/categories",
                    "path": "/categories"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_copy_in_formats(self):
        """For Release Formats, the "copy" patch has no meaning, as there is nowhere to copy to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "copy",
                    "from": "/formats",
                    "path": "/formats"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_copy_in_people(self):
        """For Release People, the "copy" patch has no real meaning. It can technically be used,
        but it makes no sense. You could only copy instruments <-> PersonID <-> ReleaseID, which is
        nonsense."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "copy",
                    "from": "/people",
                    "path": "/people"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_copy_in_songs(self):
        """For Release Songs, the "copy" patch has no real meaning. It can technically be used,
        but it makes no sense. You could only copy song duration <-> SongID <-> ReleaseID, which is
        nonsense."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "copy",
                    "from": "/songs",
                    "path": "/songs"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_move(self):
        """NOTE! More than half the columns in this project are nullable=False, which prevents
        "move" and "remove" from making the old value NULL :)
        In the Release model, only Credits, Created and Updated are nullable. But due to
        the patch basically just removing it from the dict, the patch will not remove it from DB.
        It would need to be explicitly set to null."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/credits",  # Cannot use from in a dict. It is a keyword
                    "path": "/artist"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        release = Releases.query.get_or_404(self.release_ids[0])

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest is a good and fun activity", release.Artist)

    def test_patching_using_move_in_categories(self):
        """For Release Categories, the "move" patch has no meaning, as there is nowhere to move to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/categories",
                    "path": "/categories"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_move_in_formats(self):
        """For Release Formats, the "move" patch has no meaning, as there is nowhere to move to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/formats",
                    "path": "/formats"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_move_in_people(self):
        """For Release People, the "move" patch has no meaning, as there is nowhere to move to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/people",
                    "path": "/people"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_move_in_songs(self):
        """For Release Songs, the "move" patch has no meaning, as there is nowhere to move to.
        But for full coverage, this test is needed."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "move",
                    "from": "/songs",
                    "path": "/songs"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        self.assertEquals(response.status_code, 204)
        self.assertEquals("", response.data.decode())

    def test_patching_using_remove(self):
        """NOTE! More than half the columns in this project are nullable=False, which prevents
        "move" and "remove" from making the old value NULL :)
        In the Release model, only Credits, Created and Updated are nullable"""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/artist"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        release = Releases.query.get_or_404(self.release_ids[0])

        self.assertEquals(204, response.status_code)
        self.assertNotEquals(None, release.Artist)

    def test_patching_using_remove_in_categories(self):
        """For Release Categories, the "remove" has a special own method that deletes things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/categories"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        cats = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_ids[0]).all()
        self.assertEquals(response.status_code, 204)
        self.assertEquals([], cats)

    def test_patching_using_remove_in_formats(self):
        """For Release Formats, the "remove" has a special own method that deletes things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/formats"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        formats = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_ids[0]).all()
        self.assertEquals(response.status_code, 204)
        self.assertEquals([], formats)

    def test_patching_using_remove_in_people(self):
        """For Release People, the "remove" has a special own method that deletes things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/people"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        people = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_ids[0]).all()
        self.assertEquals(response.status_code, 204)
        self.assertEquals([], people)

    def test_patching_using_remove_in_songs(self):
        """For Release Songs, the "remove" has a special own method that deletes things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "remove",
                    "path": "/songs"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        songs = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_ids[0]).all()
        self.assertEquals(response.status_code, 204)
        self.assertEquals([], songs)

    def test_patching_using_replace(self):
        """Replace will delete any existing values in the source and insert the new value there."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            data=json.dumps(
                [{
                    "op": "replace",
                    "path": "/artist",
                    "value": "UnitTest Patch Replace"
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        release = Releases.query.get_or_404(self.release_ids[0])

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest Patch Replace", release.Artist)

    def test_patching_using_replace_in_categories(self):
        """Categories has its own method for replacing things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(self.release_ids[0]),
            data=json.dumps(
                [{
                    "op": "replace",
                    "path": "/categories",
                    "value": [self.valid_cats[1], self.valid_cats[2]]
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        cats = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesCategoriesMapping.ReleaseCategoryID)
        ).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals(2, len(cats))
        self.assertEquals(self.valid_cats[1], cats[0].ReleaseCategoryID)
        self.assertEquals(self.valid_cats[2], cats[1].ReleaseCategoryID)

    def test_patching_using_replace_in_formats(self):
        """Formats has its own method for replacing things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(self.release_ids[0]),
            data=json.dumps(
                [{
                    "op": "replace",
                    "path": "/formats",
                    "value": [self.valid_formats[0], self.valid_formats[1]]
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        formats = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesFormatsMapping.ReleaseFormatID)
        ).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals(2, len(formats))
        self.assertEquals(self.valid_formats[0], formats[0].ReleaseFormatID)
        self.assertEquals(self.valid_formats[1], formats[1].ReleaseFormatID)

    def test_patching_using_replace_in_people(self):
        """People has its own method for replacing things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(self.release_ids[0]),
            data=json.dumps(
                [{
                    "op": "replace",
                    "path": "/people",
                    "value": [{self.valid_people[0]: "Bass"}, {self.valid_people[1]: "Triangle"}]
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        people = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesPeopleMapping.PersonID)
        ).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals(2, len(people))
        self.assertEquals(self.valid_people[0], people[0].PersonID)
        self.assertEquals(self.valid_people[1], people[1].PersonID)

    def test_patching_using_replace_in_songs(self):
        """Songs has its own method for replacing things."""
        response = self.app.patch(
            "/api/1.0/releases/{}".format(self.release_ids[0]),
            data=json.dumps(
                [{
                    "op": "replace",
                    "path": "/songs",
                    "value": [{self.valid_songs[0]: 55}, {self.valid_songs[1]: 167}]
                }]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        songs = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesSongsMapping.SongID)
        ).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals(2, len(songs))
        for song in songs:
            print(song.SongID)
        self.assertEquals(self.valid_songs[0], songs[0].SongID)
        self.assertEquals(self.valid_songs[1], songs[1].SongID)

    def test_patching_using_test(self):
        """Test is used to check does a resource contain the same value as our source data."""
        pass

    def test_patching_using_test_with_nonexisting_path(self):
        response = self.app.patch(
            "/api/1.0/releases/{}".format(int(self.release_ids[1])),
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

        self.assertEquals(422, response.status_code)
        self.assertFalse("", response.data.decode())

    def test_deleting_release(self):
        response = self.app.delete(
            "/api/1.0/releases/{}".format(int(self.release_ids[0])),
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        query_result = Releases.query.filter_by(ReleaseID=self.release_ids[0]).first()
        # On delete cascade should also remove the CFPS of the release ID
        cats = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesCategoriesMapping.ReleaseID)).all()
        formats = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesFormatsMapping.ReleaseID)).all()
        people = ReleasesPeopleMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesPeopleMapping.ReleaseID)).all()
        songs = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_ids[0]).order_by(
            asc(ReleasesSongsMapping.ReleaseID)).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals(None, query_result)
        self.assertEquals([], cats)
        self.assertEquals([], formats)
        self.assertEquals([], people)
        self.assertEquals([], songs)
