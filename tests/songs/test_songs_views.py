import json
import unittest

from flask_caching import Cache
from sqlalchemy import asc, or_

from app import app, db
from apps.songs.models import Songs, SongsLyrics
from apps.users.models import Users, UsersAccessTokens, UsersAccessLevels, UsersAccessMapping
from apps.utils.time import get_datetime_one_hour_ahead


class TestSongsViews(unittest.TestCase):
    def setUp(self):
        """Add some test entries to the database, so we can test getting the latest one."""

        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

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

        # Add lyrics for the first song. The mix of linebreaks is on purpose
        lyrics = SongsLyrics(
            Lyrics="My example lyrics\nAre here<br />\r\nNew paragraph\r",
            Author="UnitTester",
            SongID=entry1.SongID,
        )
        db.session.add(lyrics)
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
        """Clean up the test data we entered."""
        to_delete = Songs.query.filter(
            or_(
                Songs.Title.like("UnitTest%"),
                Songs.Title == 99,
            )
        ).all()
        for song in to_delete:
            db.session.delete(song)
        db.session.commit()

        user = Users.query.filter_by(UserID=self.user_id).first()
        db.session.delete(user)
        db.session.commit()

    def test_getting_songs_gets_all(self):
        """When you use GET /songs, it should return all songs in the DB in insert order."""
        response = self.app.get("/api/1.0/songs/")

        songs = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(3, len(songs["songs"]))
        self.assertEquals("UnitTest Song One", songs["songs"][0]["title"])
        self.assertEquals("UnitTest Song Three", songs["songs"][2]["title"])

    def test_getting_one_song(self):
        """Should return the data of a given song."""
        response = self.app.get("/api/1.0/songs/{}".format(self.valid_song_ids[0]))

        song = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(song["songs"]))
        self.assertEquals("UnitTest Song One", song["songs"][0]["title"])

    def test_getting_lyrics(self):
        """Should return the lyrics for the song with html line breaks."""
        response = self.app.get("/api/1.0/songs/{}/lyrics".format(self.valid_song_ids[0]))

        lyrics = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertTrue("songTitle" in lyrics)
        self.assertEquals("UnitTest Song One", lyrics["songTitle"])
        self.assertTrue("author" in lyrics)
        self.assertEquals(lyrics["author"], "UnitTester")
        self.assertTrue("lyrics" in lyrics)
        self.assertEquals("My example lyrics\nAre here\n\nNew paragraph\n", lyrics["lyrics"])

    def test_getting_lyrics_to_nonexisting_song(self):
        response = self.app.get("/api/1.0/songs/abc/lyrics")
        self.assertEquals(404, response.status_code)

    def test_getting_missing_lyrics_to_existing_song(self):
        response = self.app.get("/api/1.0/songs/{}/lyrics".format(self.valid_song_ids[1]))
        self.assertEquals(404, response.status_code)

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

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest Song Four", songs[3].Title)

        # Verify the result of GET after the POST
        self.assertEquals(200, get_songs.status_code)
        self.assertEquals("UnitTest Song Four", songdata["songs"][3]["title"])

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

        self.assertEquals(200, response.status_code)
        self.assertEquals(200, get_song.status_code)
        self.assertEquals("UnitTest Updated Song Two", songdata["songs"][0]["title"])
        self.assertEquals(109, songdata["songs"][0]["duration"])

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

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest Patched Song Three", song.Title)

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

        self.assertEquals(204, response.status_code)
        self.assertEquals(99, int(song.Title))

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

        self.assertEquals(422, response.status_code)
        # Make sure nothing changed.
        self.assertEquals("UnitTest Song Two", song.Title)

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

        self.assertEquals(422, response.status_code)
        # Make sure it was not removed. Although it is NOT NULL...
        self.assertEquals("UnitTest Song One", song.Title)

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

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest Patched Song Two", song.Title)

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

        self.assertEquals(204, response.status_code)
        self.assertEquals(None, song)
