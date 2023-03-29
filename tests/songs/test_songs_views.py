import json
import unittest

from flask_caching import Cache
from sqlalchemy import asc

from app import app, db
from apps.songs.models import ReleasesSongsMapping, Songs, SongsLyrics, SongsTabs
from apps.releases.models import Releases
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime_one_hour_ahead


class TestSongsViews(unittest.TestCase):
    def setUp(self):
        """Add some test entries to the database, so we can test getting the latest one."""

        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "RedisCache"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        for song in Songs.query.all():
            db.session.delete(song)
        db.session.commit()

        entry1 = Songs(
            Title="UnitTest Song One",
            Duration=99,
        )
        entry2 = Songs(
            Title="UnitTest Song Two",
            Duration=101,
        )
        entry3 = Songs(
            Title="UnitTest Song Three",
            Duration=103,
        )
        db.session.add(entry1)
        db.session.add(entry2)
        db.session.add(entry3)
        db.session.commit()

        # Create two releases for the songs
        release1 = Releases(
            ReleaseCode="VOR001",
            Title="Release One",
            Date="2022-07-07",
            Artist="Vortech",
            Credits="Created for testing",
            Created="2022-07-07 09:00:00",
            Updated=None
        )
        release2 = Releases(
            ReleaseCode="VOR002",
            Title="Release Two",
            Date="2023-01-01",
            Artist="Vortech",
            Credits="Created for testing",
            Created="2023-01-01 07:00:00",
            Updated=None
        )
        db.session.add(release1)
        db.session.add(release2)
        db.session.commit()

        # Map songs to two different releases
        mapping1 = ReleasesSongsMapping(
            ReleaseID=release1.ReleaseID,
            SongID=entry1.SongID,
            ReleaseSongDuration=123
        )
        mapping2 = ReleasesSongsMapping(
            ReleaseID=release1.ReleaseID,
            SongID=entry2.SongID,
            ReleaseSongDuration=222
        )
        mapping3 = ReleasesSongsMapping(
            ReleaseID=release2.ReleaseID,
            SongID=entry3.SongID,
            ReleaseSongDuration=321
        )
        db.session.add(mapping1)
        db.session.add(mapping2)
        db.session.add(mapping3)
        db.session.commit()

        self.valid_release_ids = []
        self.valid_release_ids.append(release1.ReleaseID)
        self.valid_release_ids.append(release2.ReleaseID)

        # Add lyrics for the songs. The mix of linebreaks is on purpose
        # and song 2 does not have lyrics on purpose.
        lyrics1 = SongsLyrics(
            Lyrics="My example lyrics\nAre here<br />\r\nNew paragraph\r",
            Author="UnitTester",
            SongID=entry1.SongID,
        )
        lyrics3 = SongsLyrics(
            Lyrics="Song 3 lyrics",
            Author="UnitTester",
            SongID=entry3.SongID,
        )
        db.session.add(lyrics1)
        db.session.add(lyrics3)
        db.session.commit()

        # Add tabs for the songs. Song 3 has no tabs on purpose.
        tab1 = SongsTabs(
            Title="Guitar Pro 5",
            Filename="utest1.gp5",
            SongID=entry1.SongID
        )
        tab2 = SongsTabs(
            Title="Guitar Pro 5",
            Filename="utest2.gp5",
            SongID=entry2.SongID
        )
        tab3 = SongsTabs(
            Title="Text",
            Filename="utest2.txt",
            SongID=entry2.SongID
        )
        db.session.add(tab1)
        db.session.add(tab2)
        db.session.add(tab3)
        db.session.commit()

        self.valid_song_ids = []
        self.valid_song_ids.append(entry1.SongID)
        self.valid_song_ids.append(entry2.SongID)
        self.valid_song_ids.append(entry3.SongID)

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
        for song in Songs.query.all():
            db.session.delete(song)
        db.session.commit()

        for mapping in ReleasesSongsMapping.query.all():
            db.session.delete(mapping)
        db.session.commit()

        for release in Releases.query.all():
            db.session.delete(release)
        db.session.commit()

        user = Users.query.filter_by(UserID=self.user_id).first()
        db.session.delete(user)
        db.session.commit()

    def test_getting_songs_gets_all(self):
        """When you use GET /songs, it should return all songs in the DB in insert order."""
        response = self.app.get("/api/1.0/songs/")

        songs = json.loads(response.get_data().decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(songs["songs"]))
        self.assertEqual("UnitTest Song One", songs["songs"][0]["title"])
        self.assertEqual("UnitTest Song Three", songs["songs"][2]["title"])

    def test_getting_one_song(self):
        """Should return the data of a given song."""
        response = self.app.get("/api/1.0/songs/{}".format(self.valid_song_ids[0]))

        song = json.loads(response.get_data().decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(song["songs"]))
        self.assertEqual("UnitTest Song One", song["songs"][0]["title"])

    def test_getting_lyrics(self):
        """Should return the lyrics for the song with html line breaks."""
        response = self.app.get("/api/1.0/songs/{}/lyrics".format(self.valid_song_ids[0]))

        lyrics = json.loads(response.get_data().decode())

        self.assertEqual(200, response.status_code)
        self.assertTrue("songTitle" in lyrics)
        self.assertEqual("UnitTest Song One", lyrics["songTitle"])
        self.assertTrue("author" in lyrics)
        self.assertEqual(lyrics["author"], "UnitTester")
        self.assertTrue("lyrics" in lyrics)
        self.assertEqual("My example lyrics\nAre here\n\nNew paragraph\n", lyrics["lyrics"])

    def test_getting_all_lyrics(self):
        """Should return every lyric in the data, organized by release."""
        response = self.app.get("/api/1.0/songs/lyrics")

        lyrics = json.loads(response.get_data().decode())

        first_album_data = lyrics["allLyrics"][0]
        first_album_first_song = first_album_data["lyrics"][0]

        second_album_data = lyrics["allLyrics"][1]
        second_album_first_song = second_album_data["lyrics"][0]

        self.assertEqual(200, response.status_code),
        self.assertTrue("allLyrics" in lyrics)
        self.assertEqual(2, len(lyrics["allLyrics"]))

        self.assertEqual(self.valid_release_ids[0], first_album_data["releaseId"])
        self.assertEqual("VOR001", first_album_data["releaseCode"])
        self.assertEqual("UnitTest Song One", first_album_first_song["songTitle"])
        self.assertEqual(
            "My example lyrics\nAre here\n\nNew paragraph\n", 
            first_album_first_song["lyrics"]
        )

        self.assertEqual(self.valid_release_ids[1], second_album_data["releaseId"])
        self.assertEqual("VOR002", second_album_data["releaseCode"])
        self.assertEqual("UnitTest Song Three", second_album_first_song["songTitle"])
        self.assertEqual("Song 3 lyrics", second_album_first_song["lyrics"])
        

    def test_getting_lyrics_to_nonexisting_song(self):
        response = self.app.get("/api/1.0/songs/abc/lyrics")
        self.assertEqual(404, response.status_code)

    def test_getting_missing_lyrics_to_existing_song(self):
        response = self.app.get("/api/1.0/songs/{}/lyrics".format(self.valid_song_ids[1]))
        self.assertEqual(404, response.status_code)

    def test_getting_tabs_with_one(self):
        """Should return the only tab for the song."""
        response = self.app.get("/api/1.0/songs/{}/tabs".format(self.valid_song_ids[0]))

        tabs = json.loads(response.get_data().decode())

        self.assertEqual(200, response.status_code)
        self.assertTrue("songTitle" in tabs)
        self.assertEqual("UnitTest Song One", tabs["songTitle"])
        self.assertTrue("tabs" in tabs)
        self.assertEqual(1, len(tabs["tabs"]))
        expected = {"title": "Guitar Pro 5", "filename": "utest1.gp5"}
        self.assertEqual(expected, tabs["tabs"][0])

    def test_getting_tabs_with_many(self):
        """Should return all tabs for the song."""
        response = self.app.get("/api/1.0/songs/{}/tabs".format(self.valid_song_ids[1]))

        tabs = json.loads(response.get_data().decode())

        self.assertEqual(200, response.status_code)
        self.assertTrue("songTitle" in tabs)
        self.assertEqual("UnitTest Song Two", tabs["songTitle"])
        self.assertTrue("tabs" in tabs)
        self.assertEqual(2, len(tabs["tabs"]))
        expected = [
            {"title": "Text", "filename": "utest2.txt"},
            {"title": "Guitar Pro 5", "filename": "utest2.gp5"}
        ]
        self.assertCountEqual(expected, tabs["tabs"])

    def test_getting_all_tabs(self):
        """Should return every tab in the data."""
        response = self.app.get("/api/1.0/songs/tabs")

        tabs = json.loads(response.get_data().decode())

        self.assertEqual(200, response.status_code),
        self.assertTrue("tabs" in tabs)
        self.assertEqual(3, len(tabs["tabs"]))
        # Note that this has two songs. One song has one tab, and the other has 2 tabs
        expected = [
            {"songId": self.valid_song_ids[0], "title": "Guitar Pro 5", "filename": "utest1.gp5"},
            {"songId": self.valid_song_ids[1], "title": "Guitar Pro 5", "filename": "utest2.gp5"},
            {"songId": self.valid_song_ids[1], "title": "Text", "filename": "utest2.txt"}
        ]
        self.assertCountEqual(expected, tabs["tabs"])
        self.assertEqual(expected[1], tabs["tabs"][1])

    def test_getting_tabs_to_nonexisting_song(self):
        response = self.app.get("/api/1.0/songs/abc/tabs")
        self.assertEqual(404, response.status_code)

    def test_getting_missing_tabs_to_existing_song(self):
        """Should return an empty array for tabs."""
        response = self.app.get("/api/1.0/songs/{}/tabs".format(self.valid_song_ids[2]))
        tabs = json.loads(response.get_data().decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual([], tabs["tabs"])

    def test_adding_songs(self):
        """Should add a new entry to the table and then GET should return them."""
        response = self.app.post(
            "/api/1.0/songs/",
            data=json.dumps(
                dict(
                    title="UnitTest Song Four",
                    duration=105,
                ),
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )
        songs = Songs.query.filter(Songs.Title.like("UnitTest%")).order_by(
            asc(Songs.SongID)
        ).all()

        get_songs = self.app.get("/api/1.0/songs/")
        songdata = json.loads(get_songs.get_data().decode())

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEqual("UnitTest Song Four", songs[3].Title)

        # Verify the result of GET after the POST
        self.assertEqual(200, get_songs.status_code)
        self.assertEqual("UnitTest Song Four", songdata["songs"][3]["title"])

    def test_updating_songs(self):
        """Should update the given entry with the data in the JSON."""
        response = self.app.put(
            "/api/1.0/songs/{}".format(self.valid_song_ids[1]),
            data=json.dumps(
                dict(
                    title="UnitTest Updated Song Two",
                    duration=109,
                )
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        get_song = self.app.get("/api/1.0/songs/{}".format(self.valid_song_ids[1]))
        songdata = json.loads(get_song.get_data().decode())

        self.assertEqual(200, response.status_code)
        self.assertEqual(200, get_song.status_code)
        self.assertEqual("UnitTest Updated Song Two", songdata["songs"][0]["title"])
        self.assertEqual(109, songdata["songs"][0]["duration"])

    def test_patching_a_song_using_add(self):
        """If the path already has a value, it is replaced. If it is empty, a new value is added.
        If it is an array, it would be appended. In the case of Songs, there is only one valid
        situation in practice: replace an existing Song title."""
        response = self.app.patch(
            "/api/1.0/songs/{}".format(self.valid_song_ids[2]),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/title",
                        value="UnitTest Patched Song Three",
                    ),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        song = Songs.query.filter_by(SongID=self.valid_song_ids[2]).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual("UnitTest Patched Song Three", song.Title)

    def test_patching_a_song_using_copy(self):
        """Copy a resource to target location. For a song, it doesn't really make sense as you can
        only copy the duration to song title."""
        response = self.app.patch(
            "/api/1.0/songs/{}".format(self.valid_song_ids[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/duration",
                        "path": "/title",
                    })
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        song = Songs.query.filter_by(SongID=self.valid_song_ids[0]).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual(99, int(song.Title))

    def test_patching_songs_using_move(self):
        """Move a resource to target location and delete source. But in Songs, there are no
        nullable columns, so move cannot be used. Thus a 422 Unprocessable Entity is returned."""
        response = self.app.patch(
            "/api/1.0/songs/{}".format(self.valid_song_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "move",
                        "from": "/title",
                        "path": "/duration",
                    }),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        song = Songs.query.filter_by(SongID=self.valid_song_ids[1]).first()

        self.assertEqual(422, response.status_code)
        # Make sure nothing changed.
        self.assertEqual("UnitTest Song Two", song.Title)

    def test_patching_a_song_using_remove(self):
        """Remove a resource. But, because both of the resources in Songs are nullable=False,
        they cannot be removed in the database. So we should return a 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/songs/{}".format(self.valid_song_ids[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "remove",
                        "path": "/title",
                    }),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        song = Songs.query.filter_by(SongID=self.valid_song_ids[0]).first()

        self.assertEqual(422, response.status_code)
        # Make sure it was not removed. Although it is NOT NULL...
        self.assertEqual("UnitTest Song One", song.Title)

    def test_patching_a_song_using_replace(self):
        """Replace the contents of a resource with a new value."""
        response = self.app.patch(
            "/api/1.0/songs/{}".format(self.valid_song_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/title",
                        "value": "UnitTest Patched Song Two"
                    }),
                ]
            ),
            content_type="application/json",
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        song = Songs.query.filter_by(SongID=self.valid_song_ids[1]).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual("UnitTest Patched Song Two", song.Title)

    # "op": "test" will be implemented later

    def test_deleting_a_song(self):
        """Should delete the song."""
        response = self.app.delete(
            "/api/1.0/songs/{}".format(self.valid_song_ids[2]),
            headers={
                'User': self.user_id,
                'Authorization': self.access_token
            }
        )

        song = Songs.query.filter_by(SongID=self.valid_song_ids[2]).first()

        self.assertEqual(204, response.status_code)
        self.assertEqual(None, song)
