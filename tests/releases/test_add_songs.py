"""CFPS = Categories, Formats, People, Songs. They are quite complex, so they were implemented
separately for the POST /releases handling. Note that ALL of the functions here insert things into
their "standalone" tables. We also test the mapping."""

import unittest

from sqlalchemy import asc

from app import db
from apps.songs.models import Songs, ReleasesSongsMapping
from apps.releases.add_cfps import add_songs
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
            ReleaseCode="TEST001"
        )
        db.session.add(release)
        db.session.commit()
        self.release_id = release.ReleaseID

        # For testing an existing song
        song = Songs(
            Title="UnitTest Song",
            Duration=99,
        )
        db.session.add(song)
        db.session.commit()
        self.existing_song_id = song.SongID

    def tearDown(self):
        songs = Songs.query.filter(
            Songs.Title.like("UnitTest%")
        ).all()
        for song in songs:
            db.session.delete(song)
        db.session.commit()

        release = Releases.query.filter_by(ReleaseID=self.release_id).first()
        db.session.delete(release)
        db.session.commit()

    def test_adding_songs_by_existing_id(self):
        """Should not add new entries to Songs, but should map the songs to the current release."""
        songs_dict = {self.existing_song_id: 240}
        add_songs(self.release_id, [songs_dict])

        songs = Songs.query.all()
        mapping = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(songs))
        self.assertEquals(1, len(mapping))
        self.assertEquals(self.existing_song_id, mapping[0].SongID)
        self.assertEquals(240, mapping[0].ReleaseSongDuration)

    def test_adding_songs_with_new_string_values(self):
        """Should create new entries to Songs and then do the mapping for the current release."""
        song1 = {"UnitTest Songie": 125}
        song2 = {"UnitTest Secunda": 290}
        songs = [song1, song2]
        add_songs(self.release_id, songs)

        songs = Songs.query.all()
        mapping = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_id).order_by(
            asc(ReleasesSongsMapping.ReleasesSongsMappingID)
        ).all()

        # Should be connected to the release
        s1 = Songs.query.filter_by(Title="UnitTest Songie").first()
        s2 = Songs.query.filter_by(Title="UnitTest Secunda").first()

        self.assertEquals(3, len(songs))
        self.assertFalse(s1 is None)
        self.assertFalse(s2 is None)
        self.assertEquals(mapping[0].SongID, s1.SongID)
        self.assertEquals(mapping[0].ReleaseSongDuration, 125)
        self.assertEquals(mapping[1].SongID, s2.SongID)
        self.assertEquals(mapping[1].ReleaseSongDuration, 290)

    def test_adding_songs_with_existing_string_values(self):
        """Should not add a new entry to Songs, and the mapping should be correct for current
        release."""
        songs_list = [{"UnitTest Song": 320}]
        add_songs(self.release_id, songs_list)

        songs = Songs.query.all()
        mapping = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(songs))
        self.assertEquals(songs[0].SongID, mapping[0].SongID)
        self.assertEquals(320, mapping[0].ReleaseSongDuration)
        # The original duration should be intact in Songs table
        self.assertEquals(99, songs[0].Duration)

    def test_adding_songs_with_nonexisting_ids(self):
        """When you add SongIDs that do not exist, no mapping should happen and no new entries
        should appear in ReleasesSongsMapping."""
        add_songs(self.release_id, [{0: 234}])

        songs = Songs.query.all()
        mapping = ReleasesSongsMapping.query.filter_by(ReleaseID=self.release_id).first()

        self.assertEquals(1, len(songs))
        self.assertTrue(mapping is None)
