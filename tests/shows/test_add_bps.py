"""BPS = Bands, People, Songs. Each is mapped via ForeignKey to a given Show.
When a new Show is added or updated, these functions get called."""

import json
import unittest

from app import db
from apps.people.models import People
from apps.shows.add_bps import add_bands, add_people, add_setlist
from apps.shows.models import Shows, ShowsOtherBands, ShowsPeopleMapping, ShowsSongsMapping
from apps.songs.models import Songs
from apps.utils.time import get_datetime


class TestAddBPS(unittest.TestCase):
    def setUp(self):
        # Add a show
        show = Shows(
            ShowDate=get_datetime(),
            CountryCode="FI",
            Country="Finland",
            City="Helsinki",
            Venue="UnitTest 7",
        )
        db.session.add(show)
        db.session.commit()
        self.valid_show_id = show.ShowID

        # Add a person
        person = People(
            Name="UnitTester"
        )
        db.session.add(person)
        db.session.commit()
        self.valid_person_id = person.PersonID

        # Add a Song
        song = Songs(
            Title="UnitTest Song",
            Duration=234,
        )
        db.session.add(song)
        db.session.commit()
        self.valid_song_id = song.SongID

    def tearDown(self):
        for show in Shows.query.filter_by(ShowID=self.valid_show_id).all():
            db.session.delete(show)
        db.session.commit()

        for person in People.query.filter_by(PersonID=self.valid_person_id).all():
            db.session.delete(person)
        db.session.commit()

        for song in Songs.query.filter_by(SongID=self.valid_song_id).all():
            db.session.delete(song)
        db.session.commit()

    def test_adding_bands(self):
        """Inserts the received band data to ShowsOtherBands. The endpoint that uses this has
        a json.loads() version of the data, so we do it that way."""
        jsondata = json.dumps([
            dict(
                bandName="UnitTest Bandy",
                bandWebsite="https://www.example.com",
            ),
            dict(
                bandName="UnitTest Yhtye",
                bandWebsite="https://www.example.com/yhtye",
            ),
        ])
        data = json.loads(jsondata)

        add_bands(self.valid_show_id, data)
        show = ShowsOtherBands.query.filter_by(ShowID=self.valid_show_id).all()

        self.assertEquals(2, len(show))
        self.assertEquals("UnitTest Bandy", show[0].BandName)
        self.assertEquals("https://www.example.com", show[0].BandWebsite)
        self.assertEquals("UnitTest Yhtye", show[1].BandName)
        self.assertEquals("https://www.example.com/yhtye", show[1].BandWebsite)

    def test_adding_people(self):
        """Inserts the received people data to ShowsPeopleMapping."""
        jsondata = json.dumps([
            dict(
                showID=self.valid_show_id,
                personID=self.valid_person_id,
                instruments="UnitTest Drums",
            ),
        ])
        data = json.loads(jsondata)

        add_people(self.valid_show_id, data)
        person = ShowsPeopleMapping.query.filter_by(ShowID=self.valid_show_id).all()

        self.assertEquals(1, len(person))
        self.assertEquals("UnitTest Drums", person[0].Instruments)
        self.assertEquals(self.valid_show_id, person[0].ShowID)
        self.assertEquals(self.valid_person_id, person[0].PersonID)

    def test_adding_songs(self):
        """Inserts the received band data to ShowsSongsMapping."""
        jsondata = json.dumps([
            dict(
                showID=self.valid_show_id,
                songID=self.valid_song_id,
                setlistOrder=1,
                duration=112,
            ),
        ])
        data = json.loads(jsondata)

        add_setlist(self.valid_show_id, data)
        song = ShowsSongsMapping.query.filter_by(ShowID=self.valid_show_id).all()

        self.assertEquals(1, len(song))
        self.assertEquals(self.valid_show_id, song[0].ShowID)
        self.assertEquals(self.valid_song_id, song[0].SongID)
        self.assertEquals(1, song[0].SetlistOrder)
        self.assertEquals(112, song[0].ShowSongDuration)
