import json
import unittest

from sqlalchemy import asc, or_

from app import app, db
from apps.people.models import People
from apps.shows.models import Shows, ShowsOtherBands, ShowsPeopleMapping, ShowsSongsMapping
from apps.songs.models import Songs
from apps.utils.time import get_datetime


class TestShowsViews(unittest.TestCase):
    def setUp(self):
        """Add some test entries to the database, so we can test getting the latest one."""
        self.app = app.test_client()

        entry1 = Shows(
            ShowDate=get_datetime(),
            CountryCode="FI",
            Country="Finland",
            City="Espoo",
            Venue="UnitTest 1",
        )
        entry2 = Shows(
            ShowDate=get_datetime(),
            CountryCode="SE",
            Country="Sweden",
            City="Stockholm",
            Venue="UnitTest 2",
        )
        entry3 = Shows(
            ShowDate=get_datetime(),
            CountryCode="NO",
            Country="Norway",
            City="Oslo",
            Venue="UnitTest 3",
        )

        db.session.add(entry1)
        db.session.add(entry2)
        db.session.add(entry3)
        db.session.commit()

        self.valid_show_ids = []
        self.valid_show_ids.append(entry1.ShowID)
        self.valid_show_ids.append(entry2.ShowID)
        self.valid_show_ids.append(entry3.ShowID)

        # We need a valid Person
        person = People(
            Name="UnitTester"
        )
        db.session.add(person)
        db.session.commit()
        self.valid_person_id = person.PersonID

        # And a valid Song
        song = Songs(
            Title="UnitTest Song",
            Duration=234,
        )
        db.session.add(song)
        db.session.commit()
        self.valid_song_id = song.SongID

        # Then add Bands, People and Songs to them
        bands_show1 = ShowsOtherBands(
            ShowID=entry1.ShowID,
            BandName="UnitTest Band1",
            BandWebsite="https://www.example.com/band1",
        )
        people_show1 = ShowsPeopleMapping(
            ShowID=entry1.ShowID,
            PersonID=self.valid_person_id,
            Instruments="UnitTest Bass",
        )
        songs_show1 = ShowsSongsMapping(
            ShowID=entry1.ShowID,
            SongID=self.valid_song_id,
            SetlistOrder=1,
            ShowSongDuration=230,
        )
        db.session.add(bands_show1)
        db.session.add(people_show1)
        db.session.add(songs_show1)
        db.session.commit()

        bands_show2 = ShowsOtherBands(
            ShowID=entry2.ShowID,
            BandName="UnitTest Band2",
            BandWebsite="https://www.example.com/band2",
        )
        people_show2 = ShowsPeopleMapping(
            ShowID=entry2.ShowID,
            PersonID=self.valid_person_id,
            Instruments="UnitTest Drum and Bass",
        )
        songs_show2 = ShowsSongsMapping(
            ShowID=entry2.ShowID,
            SongID=self.valid_song_id,
            SetlistOrder=1,
            ShowSongDuration=231,
        )
        db.session.add(bands_show2)
        db.session.add(people_show2)
        db.session.add(songs_show2)
        db.session.commit()

        bands_show3 = ShowsOtherBands(
            ShowID=entry3.ShowID,
            BandName="UnitTest Band3",
            BandWebsite="https://www.example.com/band3",
        )
        people_show3 = ShowsPeopleMapping(
            ShowID=entry3.ShowID,
            PersonID=self.valid_person_id,
            Instruments="UnitTest Shaker",
        )
        songs_show3 = ShowsSongsMapping(
            ShowID=entry3.ShowID,
            SongID=self.valid_song_id,
            SetlistOrder=1,
            ShowSongDuration=237,
        )
        db.session.add(bands_show3)
        db.session.add(people_show3)
        db.session.add(songs_show3)
        db.session.commit()

    def tearDown(self):
        """Clean up the test data we entered."""
        for show in Shows.query.filter(
            or_(
                Shows.Venue.like("UnitTest%"),
                Shows.Venue == "Finland"
            )
        ).all():
            db.session.delete(show)
        db.session.commit()

        for person in People.query.filter(People.Name.like("UnitTest%")).all():
            db.session.delete(person)

        for song in Songs.query.filter(Songs.Title.like("UnitTest%")).all():
            db.session.delete(song)

        for band in ShowsOtherBands.query.filter(
            ShowsOtherBands.BandName.like("UnitTest%")
        ).all():
            db.session.delete(band)

    def test_getting_shows_gets_all(self):
        """When you use GET /shows, it should return all shows in the DB in insert order."""
        response = self.app.get("/api/1.0/shows/")

        shows = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(3, len(shows["shows"]))
        self.assertEquals("UnitTest 1", shows["shows"][0]["venue"])
        self.assertEquals("UnitTest 3", shows["shows"][2]["venue"])
        self.assertEquals("UnitTest Band3", shows["shows"][2]["otherBands"][0]["name"])
        self.assertEquals("UnitTest Shaker", shows["shows"][2]["people"][0]["instruments"])
        self.assertEquals(237, shows["shows"][2]["setlist"][0]["duration"])

    def test_getting_one_show(self):
        """Should return the data of a given show."""
        response = self.app.get("/api/1.0/shows/{}".format(self.valid_show_ids[0]))

        show = json.loads(response.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(show["shows"]))
        self.assertEquals("UnitTest 1", show["shows"][0]["venue"])
        self.assertEquals("UnitTest Band1", show["shows"][0]["otherBands"][0]["name"])
        self.assertEquals("UnitTest Bass", show["shows"][0]["people"][0]["instruments"])
        self.assertEquals(230, show["shows"][0]["setlist"][0]["duration"])

    def test_adding_shows(self):
        """Should add a new entry to the table and then GET should return them. The extra details
        "otherBands", "people", and "setlist" are optional, and this should work without them."""
        response = self.app.post(
            "/api/1.0/shows/",
            data=json.dumps(
                dict(
                    showDate=get_datetime(),
                    countryCode="DK",
                    country="Denmark",
                    city="Copenhagen",
                    venue="UnitTest 4",
                ),
            ),
            content_type="application/json"
        )
        shows = Shows.query.filter(Shows.Venue.like("UnitTest%")).order_by(
            asc(Shows.ShowID)
        ).all()

        get_shows = self.app.get("/api/1.0/shows/")
        showdata = json.loads(get_shows.get_data().decode())

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest 4", shows[3].Venue)

        # Verify the result of GET after the POST
        self.assertEquals(200, get_shows.status_code)
        self.assertEquals("UnitTest 4", showdata["shows"][3]["venue"])

    def test_updating_shows(self):
        """Should update the given entry with the data in the JSON."""
        response = self.app.put(
            "/api/1.0/shows/{}".format(self.valid_show_ids[1]),
            data=json.dumps(
                dict(
                    showDate=get_datetime(),
                    countryCode="DE",
                    country="Germany",
                    city="Berlin",
                    venue="UnitTest 5",
                )
            ),
            content_type="application/json"
        )

        get_show = self.app.get("/api/1.0/shows/{}".format(self.valid_show_ids[1]))
        showdata = json.loads(get_show.get_data().decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(200, get_show.status_code)
        self.assertEquals("UnitTest 5", showdata["shows"][0]["venue"])
        self.assertEquals("Germany", showdata["shows"][0]["country"])

    def test_patching_a_show_using_add(self):
        """If the path already has a value, it is replaced. If it is empty, a new value is added.
        If it is an array, it would be appended. In the case of Shows, there are many situations
        when all three are needed. When a show is first added, it only has the basic data. When
        more details come up, the Show will be updated with entries that very likely go to one or
        all of the three related tables: ShowsSongsMapping, ShowsOtherBands, or ShowsPeopleMapping.
        """
        response = self.app.patch(
            "/api/1.0/shows/{}".format(self.valid_show_ids[2]),
            data=json.dumps(
                [
                    dict(
                        op="add",
                        path="/venue",
                        value="UnitTest 6",
                    ),
                    dict(
                        op="add",
                        path="/otherBands",
                        value=[
                            {"UnitTest X8": "http://www.example.com"}
                        ]
                    ),
                    dict(
                        op="add",
                        path="/setlist",
                        value=[
                            {"Song 1": 123},
                            {"Song 2": 320},
                            {"Song 3": 115},
                        ]
                    ),
                    dict(
                        op="add",
                        path="/people",
                        value={"UnitTest Man": "Drums"}
                    ),
                ]
            ),
            content_type="application/json"
        )

        show = Shows.query.filter_by(ShowID=self.valid_show_ids[2]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("UnitTest 6", show.Venue)
        # TODO: Check the joined tables too

    def test_patching_a_show_using_copy(self):
        """Copy a resource to target location."""
        # TODO: Add tests for joined tables.
        response = self.app.patch(
            "/api/1.0/shows/{}".format(self.valid_show_ids[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/country",
                        "path": "/venue",
                    })
                ]
            ),
            content_type="application/json"
        )

        show = Shows.query.filter_by(ShowID=self.valid_show_ids[0]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("Finland", show.Venue)

    def test_patching_shwos_using_move(self):
        """Move a resource to target location and delete source."""
        response = self.app.patch(
            "/api/1.0/shows/{}".format(self.valid_show_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "move",
                        "from": "/countryCode",
                        "path": "/city",
                    }),
                ]
            ),
            content_type="application/json"
        )

        show = Shows.query.filter_by(ShowID=self.valid_show_ids[1]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("SE", show.City)

    def test_patching_a_show_using_remove(self):
        """Remove a resource. Most of the columns are NOT NULL though..."""
        response = self.app.patch(
            "/api/1.0/shows/{}".format(self.valid_show_ids[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "remove",
                        "path": "/venue",
                    }),
                ]
            ),
            content_type="application/json"
        )

        self.assertEquals(204, response.status_code)

    def test_patching_a_show_using_replace(self):
        """Replace the contents of a resource with a new value."""
        response = self.app.patch(
            "/api/1.0/shows/{}".format(self.valid_show_ids[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/country",
                        "value": "Switzerland"
                    }),
                ]
            ),
            content_type="application/json"
        )

        show = Shows.query.filter_by(ShowID=self.valid_show_ids[1]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("Switzerland", show.Country)

    # "op": "test" will be implemented later

    def test_deleting_a_show(self):
        """Should delete the show."""
        response = self.app.delete("/api/1.0/shows/{}".format(self.valid_show_ids[2]))

        show = Shows.query.filter_by(ShowID=self.valid_show_ids[2]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals(None, show)

    def test_adding_show_with_bands_people_setlist(self):
        """Add a show with BPS included."""
        response = self.app.post(
            "/api/1.0/shows/",
            data=json.dumps(
                dict(
                    showDate=get_datetime(),
                    countryCode="DK",
                    country="Denmark",
                    city="Copenhagen",
                    venue="UnitTest 4",
                    otherBands=[
                        {"bandName": "My First Band", "bandWebsite": "https://www.example.com"},
                        {"bandName": "Metallica", "bandWebsite": "http://www.metallica.com"}
                    ],
                    people=[
                        {"personID": self.valid_person_id, "instruments": "UnitTest Guitar"}
                    ],
                    setlist=[
                        {"songID": self.valid_song_id, "setlistOrder": 1, "duration": 210}
                    ]
                ),
            ),
            content_type="application/json"
        )
        shows = Shows.query.filter(Shows.Venue.like("UnitTest%")).order_by(
            asc(Shows.ShowID)
        ).all()

        get_shows = self.app.get("/api/1.0/shows/")
        showdata = json.loads(get_shows.get_data().decode())
        print(showdata)

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.get_data().decode())
        self.assertEquals("UnitTest 4", shows[3].Venue)

        # Verify the result of GET after the POST
        self.assertEquals(200, get_shows.status_code)
        self.assertEquals("UnitTest 4", showdata["shows"][3]["venue"])
        self.assertEquals("My First Band", showdata["shows"][3]["otherBands"][0]["name"])
        self.assertEquals("Metallica", showdata["shows"][3]["otherBands"][1]["name"])
        self.assertEquals(self.valid_person_id, showdata["shows"][3]["people"][0]["personID"])
        self.assertEquals("UnitTest Guitar", showdata["shows"][3]["people"][0]["instruments"])
        self.assertEquals(self.valid_song_id, showdata["shows"][3]["setlist"][0]["songID"])
        self.assertEquals(210, showdata["shows"][3]["setlist"][0]["duration"])

    def test_updating_show_with_bands_people_setlist(self):
        """Update a show with BPS included."""
        response = self.app.put(
            "/api/1.0/shows/{}".format(self.valid_show_ids[1]),
            data=json.dumps(
                dict(
                    showDate=get_datetime(),
                    countryCode="DE",
                    country="Germany",
                    city="Berlin",
                    venue="UnitTest 5",
                    otherBands=[
                        {"bandName": "My First Band", "bandWebsite": "https://www.example.com"},
                        {"bandName": "Metallica", "bandWebsite": "http://www.metallica.com"}
                    ],
                    people=[
                        {"personID": self.valid_person_id, "instruments": "UnitTest Guitar"}
                    ],
                    setlist=[
                        {"songID": self.valid_song_id, "setlistOrder": 1, "duration": 210}
                    ]
                )
            ),
            content_type="application/json"
        )

        get_show = self.app.get("/api/1.0/shows/{}".format(self.valid_show_ids[1]))
        showdata = json.loads(get_show.get_data().decode())
        print(showdata)

        self.assertEquals(200, response.status_code)
        self.assertEquals(200, get_show.status_code)
        self.assertEquals("UnitTest 5", showdata["shows"][0]["venue"])
        self.assertEquals("Germany", showdata["shows"][0]["country"])
        self.assertEquals("My First Band", showdata["shows"][0]["otherBands"][0]["name"])
        self.assertEquals("Metallica", showdata["shows"][0]["otherBands"][1]["name"])
        self.assertEquals("UnitTest Guitar", showdata["shows"][0]["people"][0]["instruments"])
        self.assertEquals(self.valid_song_id, showdata["shows"][0]["setlist"][0]["songID"])
        self.assertEquals(210, showdata["shows"][0]["setlist"][0]["duration"])

    def test_patching_with_exception(self):
        """Test a patch that results in 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/shows/{}".format(int(self.valid_show_ids[0])),
            data=json.dumps(
                [{
                    "op": "test",
                    "path": "/doesnotexist",
                    "value": "I do not exist"
                }]
            ),
            content_type="application/json"
        )

        self.assertEquals(422, response.status_code)
        self.assertFalse("", response.data.decode())
