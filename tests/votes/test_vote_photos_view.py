import json
import unittest
from sqlalchemy import asc

from app import app, db
from apps.photos.models import Photos
from apps.users.models import Users, UsersAccessLevels, UsersAccessMapping, UsersAccessTokens
from apps.votes.models import VotesPhotos
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestVotePhotosView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        # Add three photos
        photo1 = Photos(
            Image="unittest1.jpg",
            Caption="UnitTest1",
            TakenBy="Unittester",
            Country="Finland",
            CountryCode="FI",
            City="Espoo",
            Created=get_datetime(),
        )
        photo2 = Photos(
            Image="unittest2.jpg",
            Caption="UnitTest2",
            TakenBy="Unittester",
            Country="Finland",
            CountryCode="FI",
            City="Espoo",
            Created=get_datetime(),
        )
        photo3 = Photos(
            Image="unittest3.jpg",
            Caption="UnitTest3",
            TakenBy="Unittester",
            Country="Finland",
            CountryCode="FI",
            City="Espoo",
            Created=get_datetime(),
        )
        db.session.add(photo1)
        db.session.add(photo2)
        db.session.add(photo3)
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

        self.photo_ids = [photo1.PhotoID, photo2.PhotoID, photo3.PhotoID]

        # Add some votes for each photo - minimum is 1.0, maximum is 5.0. The real steps will be
        # in 0.5 increments. However, any 2 decimal float between 1.00 and 5.00 is technically ok.
        p1_vote1 = VotesPhotos(
            PhotoID=self.photo_ids[0], Vote=4, UserID=self.guest_id, Created=get_datetime())
        p1_vote2 = VotesPhotos(
            PhotoID=self.photo_ids[0], Vote=3.0, UserID=self.guest_id, Created=get_datetime())
        p1_vote3 = VotesPhotos(
            PhotoID=self.photo_ids[0], Vote=3.00, UserID=self.guest_id, Created=get_datetime())
        p2_vote1 = VotesPhotos(
            PhotoID=self.photo_ids[1], Vote=5, UserID=self.guest_id, Created=get_datetime())
        p3_vote1 = VotesPhotos(
            PhotoID=self.photo_ids[2], Vote=4, UserID=self.guest_id, Created=get_datetime())
        p3_vote2 = VotesPhotos(
            PhotoID=self.photo_ids[2], Vote=1, UserID=self.guest_id, Created=get_datetime())

        # Add an existing vote for the registered user
        p3_reg_vote = VotesPhotos(
            PhotoID=self.photo_ids[2], Vote=4, UserID=self.valid_reg_user,
            Created=get_datetime()
        )

        db.session.add(p1_vote1)
        db.session.add(p1_vote2)
        db.session.add(p1_vote3)
        db.session.add(p2_vote1)
        db.session.add(p3_vote1)
        db.session.add(p3_vote2)
        db.session.add(p3_reg_vote)
        db.session.commit()

    def tearDown(self):
        # Deleting a photo will also delete the votes for it
        for photo in Photos.query.filter(Photos.Caption.like("UnitTest%")).all():
            db.session.delete(photo)
        db.session.commit()

        for user in Users.query.filter(Users.Username.like("unittest%")).all():
            db.session.delete(user)
        db.session.commit()

        access = UsersAccessLevels.query.filter_by(LevelName="Registered").first()
        db.session.delete(access)
        db.session.commit()

    def test_getting_all_votes(self):
        """Should return the current votes for all Photos."""
        response = self.app.get("/api/1.0/votes/photos/")
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(3, len(data["votes"]))
        self.assertEquals(self.photo_ids[0], data["votes"][0]["PhotoID"])
        self.assertEquals(3, data["votes"][0]["voteCount"])
        self.assertEquals(3.33, data["votes"][0]["rating"])

        self.assertEquals(self.photo_ids[2], data["votes"][2]["PhotoID"])
        self.assertEquals(3, data["votes"][2]["voteCount"])
        self.assertEquals(3, data["votes"][2]["rating"])

    def test_getting_votes_for_one_photo(self):
        """Should return the votes for the specified photo."""
        response = self.app.get("/api/1.0/votes/photos/{}".format(self.photo_ids[1]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(1, len(data["votes"]))
        self.assertEquals(self.photo_ids[1], data["votes"][0]["photoID"])
        self.assertEquals(1, data["votes"][0]["voteCount"])
        self.assertEquals(5, data["votes"][0]["rating"])

    def test_adding_a_vote_as_guest(self):
        """Should add a new vote for the specified photo, which is given in the JSON."""
        response = self.app.post(
            "/api/1.0/votes/photos/",
            data=json.dumps(
                dict(
                    PhotoID=self.photo_ids[1],
                    rating=4,
                )
            ),
            content_type="application/json"
        )

        votes = VotesPhotos.query.filter_by(PhotoID=self.photo_ids[1]).order_by(
            asc(VotesPhotos.VoteID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.data.decode())
        self.assertEquals(2, len(votes))
        self.assertEquals(5.00, float(votes[0].Vote))
        self.assertEquals(4.00, float(votes[1].Vote))

    def test_adding_a_vote_as_registered_user(self):
        """Should add a new vote with the userID."""
        response = self.app.post(
            "/api/1.0/votes/photos/",
            data=json.dumps(
                dict(
                    PhotoID=self.photo_ids[1],
                    rating=3.5,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        votes = VotesPhotos.query.filter_by(PhotoID=self.photo_ids[1]).order_by(
            asc(VotesPhotos.VoteID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertEquals(2, len(votes))
        self.assertEquals(5.00, float(votes[0].Vote))
        self.assertEquals(3.50, float(votes[1].Vote))

    def test_adding_a_vote_as_registered_user_with_invalid_token(self):
        """Should throw a 401, since it is an invalid case."""
        response = self.app.post(
            "/api/1.0/votes/photos/",
            data=json.dumps(
                dict(
                    PhotoID=self.photo_ids[1],
                    rating=3.5,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": "not valid"
            }
        )

        votes = VotesPhotos.query.filter_by(PhotoID=self.photo_ids[1]).order_by(
            asc(VotesPhotos.VoteID)
        ).all()

        self.assertEquals(401, response.status_code)
        self.assertEquals(1, len(votes))
        self.assertEquals(5.00, float(votes[0].Vote))

    def test_adding_another_vote_as_registered_user_for_same_photo(self):
        """Should replace the existing vote with the new one."""
        response = self.app.post(
            "/api/1.0/votes/photos/",
            data=json.dumps(
                dict(
                    PhotoID=self.photo_ids[2],
                    rating=3,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        votes = VotesPhotos.query.filter_by(PhotoID=self.photo_ids[2]).order_by(
            asc(VotesPhotos.VoteID)
        ).all()

        votes_by_reg = VotesPhotos.query.filter(
            VotesPhotos.PhotoID == self.photo_ids[2],
            VotesPhotos.UserID == self.valid_reg_user
        ).order_by(
            asc(VotesPhotos.VoteID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertEquals(3, len(votes))
        self.assertEquals(4.00, float(votes[0].Vote))
        self.assertEquals(1.00, float(votes[1].Vote))
        # This was originally 4.00 in setUp, and after the POST, should be 3.00
        self.assertEquals(3.00, float(votes[2].Vote))
        self.assertEquals(1, len(votes_by_reg))
