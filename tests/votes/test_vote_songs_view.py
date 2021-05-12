import json
import unittest

from flask_caching import Cache
from sqlalchemy import asc

from app import app, db
from apps.songs.models import Songs
from apps.users.models import Users, UsersAccessLevels, UsersAccessMapping, UsersAccessTokens
from apps.votes.models import VotesSongs
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestVoteSongsView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "RedisCache"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Add three songs
        song1 = Songs(
            Title="UnitTest1",
            Duration=123,
        )
        song2 = Songs(
            Title="UnitTest2",
            Duration=123,
        )
        song3 = Songs(
            Title="UnitTest3",
            Duration=123,
        )
        song4 = Songs(
            Title="UnitTest4",
            Duration=123,
        )
        db.session.add(song1)
        db.session.add(song2)
        db.session.add(song3)
        db.session.add(song4)
        db.session.commit()

        # Add a guest and registered user, and a test token for the registered
        # Guest userID must be 1
        user_guest = Users(
            UserID=1,
            Name="UnitTest guest",
            Username="unittester-guest",
            Password="unittest",
            Created=get_datetime(),
        )
        user_reg = Users(
            Name="UnitTest2 reg",
            Username="unittester2-reg",
            Password="unittest2",
            Created=get_datetime(),
        )
        db.session.add(user_guest)
        db.session.add(user_reg)
        db.session.commit()

        # Make user_reg a registered user with a token
        if not UsersAccessLevels.query.filter_by(LevelName="Registered").first():
            registered = UsersAccessLevels(
                UsersAccessLevelID=2,
                LevelName="Registered"
            )
            db.session.add(registered)
            db.session.commit()

        grant_registered = UsersAccessMapping(
            UserID=user_reg.UserID,
            UsersAccessLevelID=2
        )

        self.access_token = "unittest-access-token"
        user_token = UsersAccessTokens(
            UserID=user_reg.UserID,
            AccessToken=self.access_token,
            ExpirationDate=get_datetime_one_hour_ahead()
        )

        db.session.add(grant_registered)
        db.session.add(user_token)
        db.session.commit()

        self.valid_reg_user = user_reg.UserID
        self.valid_token = self.access_token
        self.guest_id = user_guest.UserID

        self.song_ids = [song1.SongID, song2.SongID, song3.SongID]
        self.song_without_votes = song4.SongID

        # Add some votes for each song - minimum is 1.0, maximum is 5.0. The real steps will be
        # in 0.5 increments. However, any 2 decimal float between 1.00 and 5.00 is technically ok.
        s1_vote1 = VotesSongs(
            SongID=self.song_ids[0], Vote=4, UserID=self.guest_id, Created=get_datetime())
        s1_vote2 = VotesSongs(
            SongID=self.song_ids[0], Vote=3.0, UserID=self.guest_id, Created=get_datetime())
        s1_vote3 = VotesSongs(
            SongID=self.song_ids[0], Vote=3.00, UserID=self.guest_id, Created=get_datetime())
        s2_vote1 = VotesSongs(
            SongID=self.song_ids[1], Vote=5, UserID=self.guest_id, Created=get_datetime())
        s3_vote1 = VotesSongs(
            SongID=self.song_ids[2], Vote=4, UserID=self.guest_id, Created=get_datetime())
        s3_vote2 = VotesSongs(
            SongID=self.song_ids[2], Vote=1, UserID=self.guest_id, Created=get_datetime())

        # Add an existing vote for the registered user
        s3_reg_vote = VotesSongs(
            SongID=self.song_ids[2], Vote=4, UserID=self.valid_reg_user,
            Created=get_datetime()
        )

        db.session.add(s1_vote1)
        db.session.add(s1_vote2)
        db.session.add(s1_vote3)
        db.session.add(s2_vote1)
        db.session.add(s3_vote1)
        db.session.add(s3_vote2)
        db.session.add(s3_reg_vote)
        db.session.commit()

    def tearDown(self):
        # Deleting a song will also delete the votes for it
        for song in Songs.query.all():
            db.session.delete(song)
        db.session.commit()

        for user in Users.query.all():
            db.session.delete(user)
        db.session.commit()

        access = UsersAccessLevels.query.filter_by(LevelName="Registered").first()
        db.session.delete(access)
        db.session.commit()

    def test_getting_all_votes(self):
        """Should return the current votes for all Songs."""
        response = self.app.get("/api/1.0/votes/songs/")
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertEqual(4, len(data["votes"]))
        self.assertEqual(self.song_ids[0], data["votes"][0]["songID"])
        self.assertEqual(3, data["votes"][0]["voteCount"])
        self.assertEqual(3.33, data["votes"][0]["rating"])

        self.assertEqual(self.song_ids[2], data["votes"][2]["songID"])
        self.assertEqual(3, data["votes"][2]["voteCount"])
        self.assertEqual(3, data["votes"][2]["rating"])

    def test_getting_votes_for_one_song(self):
        """Should return the votes for the specified song."""
        response = self.app.get("/api/1.0/votes/songs/{}".format(self.song_ids[1]))
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertEqual(1, len(data["votes"]))
        self.assertEqual(self.song_ids[1], data["votes"][0]["songID"])
        self.assertEqual(1, data["votes"][0]["voteCount"])
        self.assertEqual(5, data["votes"][0]["rating"])

    def test_getting_votes_for_song_without_votes(self):
        """Should return an empty object."""
        response = self.app.get("/api/1.0/votes/songs/{}".format(self.song_without_votes))
        data = json.loads(response.data.decode())

        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, data)
        self.assertEqual(1, len(data["votes"]))
        self.assertEqual(self.song_without_votes, data["votes"][0]["songID"])
        self.assertEqual(0, data["votes"][0]["voteCount"])
        self.assertEqual(0, data["votes"][0]["rating"])

    def test_adding_a_vote_as_guest(self):
        """Should add a new vote for the specified song, which is given in the JSON."""
        response = self.app.post(
            "/api/1.0/votes/songs/",
            data=json.dumps(
                dict(
                    songID=self.song_ids[1],
                    rating=4,
                )
            ),
            content_type="application/json"
        )

        votes = VotesSongs.query.filter_by(SongID=self.song_ids[1]).order_by(
            asc(VotesSongs.VoteID)
        ).all()

        self.assertEqual(201, response.status_code)
        self.assertTrue("Location" in response.data.decode())
        self.assertEqual(2, len(votes))
        self.assertEqual(5.00, float(votes[0].Vote))
        self.assertEqual(4.00, float(votes[1].Vote))

    def test_adding_a_vote_as_registered_user(self):
        """Should add a new vote with the userID."""
        response = self.app.post(
            "/api/1.0/votes/songs/",
            data=json.dumps(
                dict(
                    songID=self.song_ids[1],
                    rating=3.5,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        votes = VotesSongs.query.filter_by(SongID=self.song_ids[1]).order_by(
            asc(VotesSongs.VoteID)
        ).all()

        self.assertEqual(201, response.status_code)
        self.assertEqual(2, len(votes))
        self.assertEqual(5.00, float(votes[0].Vote))
        self.assertEqual(3.50, float(votes[1].Vote))

    def test_adding_a_vote_as_registered_user_with_invalid_token(self):
        """Should throw a 401, since it is an invalid case."""
        response = self.app.post(
            "/api/1.0/votes/songs/",
            data=json.dumps(
                dict(
                    songID=self.song_ids[1],
                    rating=3.5,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": "not valid"
            }
        )

        votes = VotesSongs.query.filter_by(SongID=self.song_ids[1]).order_by(
            asc(VotesSongs.VoteID)
        ).all()

        self.assertEqual(401, response.status_code)
        self.assertEqual(1, len(votes))
        self.assertEqual(5.00, float(votes[0].Vote))

    def test_adding_another_vote_as_registered_user_for_same_song(self):
        """Should replace the existing vote with the new one."""
        response = self.app.post(
            "/api/1.0/votes/songs/",
            data=json.dumps(
                dict(
                    songID=self.song_ids[2],
                    rating=3,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        votes = VotesSongs.query.filter_by(SongID=self.song_ids[2]).order_by(
            asc(VotesSongs.VoteID)
        ).all()

        votes_by_reg = VotesSongs.query.filter(
            VotesSongs.SongID == self.song_ids[2],
            VotesSongs.UserID == self.valid_reg_user
        ).order_by(
            asc(VotesSongs.VoteID)
        ).all()

        self.assertEqual(201, response.status_code)
        self.assertEqual(3, len(votes))
        self.assertEqual(4.00, float(votes[0].Vote))
        self.assertEqual(1.00, float(votes[1].Vote))
        # This was originally 4.00 in setUp, and after the POST, should be 3.00
        self.assertEqual(3.00, float(votes[2].Vote))
        self.assertEqual(1, len(votes_by_reg))
