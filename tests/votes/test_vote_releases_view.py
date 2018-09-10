import json
import unittest

from flask_caching import Cache
from sqlalchemy import asc

from app import app, db
from apps.releases.models import Releases
from apps.users.models import Users, UsersAccessLevels, UsersAccessMapping, UsersAccessTokens
from apps.votes.models import VotesReleases
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead


class TestVoteReleasesView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        # Clear redis cache completely
        cache = Cache()
        cache.init_app(app, config={"CACHE_TYPE": "redis"})
        with app.app_context():
            cache.clear()

        self.app = app.test_client()

        # Add three releases
        release1 = Releases(
            Title="UnitTest 1",
            Date=get_datetime(),
            Artist="UnitTest Arts 1",
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
        release3 = Releases(
            Title="UnitTest 3",
            Date=get_datetime(),
            Artist="UnitTest 3 Arts",
            Credits="UnitTest three's a crowd",
            Created=get_datetime(),
            ReleaseCode="TEST003"
        )
        release4 = Releases(
            Title="UnitTest 4",
            Date=get_datetime(),
            Artist="UnitTest 4 Arts",
            Credits="UnitTest foursome",
            Created=get_datetime(),
            ReleaseCode="TEST004"
        )
        db.session.add(release1)
        db.session.add(release2)
        db.session.add(release3)
        db.session.add(release4)
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

        self.release_ids = [release1.ReleaseID, release2.ReleaseID, release3.ReleaseID]
        self.release_without_votes = release4.ReleaseID

        # Add some votes for each release - minimum is 1.0, maximum is 5.0. The real steps will be
        # in 0.5 increments. However, any 2 decimal float between 1.00 and 5.00 is technically ok.
        rel1_vote1 = VotesReleases(
            ReleaseID=self.release_ids[0], Vote=4, UserID=self.guest_id, Created=get_datetime())
        rel1_vote2 = VotesReleases(
            ReleaseID=self.release_ids[0], Vote=3.0, UserID=self.guest_id, Created=get_datetime())
        rel1_vote3 = VotesReleases(
            ReleaseID=self.release_ids[0], Vote=3.00, UserID=self.guest_id, Created=get_datetime()
        )
        rel2_vote1 = VotesReleases(
            ReleaseID=self.release_ids[1], Vote=5, UserID=self.guest_id, Created=get_datetime())
        rel3_vote1 = VotesReleases(
            ReleaseID=self.release_ids[2], Vote=4, UserID=self.guest_id, Created=get_datetime())
        rel3_vote2 = VotesReleases(
            ReleaseID=self.release_ids[2], Vote=1, UserID=self.guest_id, Created=get_datetime())

        # Add an existing vote for the registered user
        rel3_reg_vote = VotesReleases(
            ReleaseID=self.release_ids[2], Vote=4, UserID=self.valid_reg_user,
            Created=get_datetime()
        )

        db.session.add(rel1_vote1)
        db.session.add(rel1_vote2)
        db.session.add(rel1_vote3)
        db.session.add(rel2_vote1)
        db.session.add(rel3_vote1)
        db.session.add(rel3_vote2)
        db.session.add(rel3_reg_vote)
        db.session.commit()

    def tearDown(self):
        # Deleting a release will also delete the votes for it
        for release in Releases.query.filter(Releases.Title.like("UnitTest%")).all():
            db.session.delete(release)
        db.session.commit()

        for user in Users.query.filter(Users.Username.like("unittest%")).all():
            db.session.delete(user)
        db.session.commit()

        access = UsersAccessLevels.query.filter_by(LevelName="Registered").first()
        db.session.delete(access)
        db.session.commit()

    def test_getting_all_votes(self):
        """Should return the current votes for all releases."""
        response = self.app.get("/api/1.0/votes/releases/")
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(4, len(data["votes"]))
        self.assertEquals(self.release_ids[0], data["votes"][0]["releaseID"])
        self.assertEquals(3, data["votes"][0]["voteCount"])
        self.assertEquals(3.33, data["votes"][0]["rating"])

        self.assertEquals(self.release_ids[2], data["votes"][2]["releaseID"])
        self.assertEquals(3, data["votes"][2]["voteCount"])
        self.assertEquals(3, data["votes"][2]["rating"])

    def test_getting_votes_for_one_release(self):
        """Should return the votes for the specified release."""
        response = self.app.get("/api/1.0/votes/releases/{}".format(self.release_ids[1]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(1, len(data["votes"]))
        self.assertEquals(self.release_ids[1], data["votes"][0]["releaseID"])
        self.assertEquals(1, data["votes"][0]["voteCount"])
        self.assertEquals(5, data["votes"][0]["rating"])

    def test_getting_vote_info_as_registered_user(self):
        """A registered, logged in user can retrieve the vote he has given for a release."""
        response = self.app.get(
            "/api/1.0/users/{}/votes/releases/{}".format(self.valid_reg_user, self.release_ids[2]),
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertTrue("voteID" in data)
        self.assertTrue("vote" in data)
        self.assertTrue("releaseID" in data)
        self.assertEquals(4.0, data["vote"])
        self.assertNotEquals(None, data["created_at"])

    def test_getting_vote_info_nonexisting_user(self):
        """Should be 404."""
        response = self.app.get(
            "/api/1.0/users/abc/votes/releases/{}".format(self.release_ids[2]),
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        self.assertEquals(404, response.status_code)

    def test_getting_vote_info_nonexisting_release(self):
        """Should be 404."""
        response = self.app.get(
            "/api/1.0/users/{}/votes/releases/abc".format(self.valid_reg_user),
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        self.assertEquals(404, response.status_code)

    def test_getting_votes_for_release_without_votes(self):
        """Should return an empty object."""
        response = self.app.get("/api/1.0/votes/releases/{}".format(self.release_without_votes))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(1, len(data["votes"]))
        self.assertEquals(self.release_without_votes, data["votes"][0]["releaseID"])
        self.assertEquals(0, data["votes"][0]["voteCount"])
        self.assertEquals(0, data["votes"][0]["rating"])

    def test_adding_a_vote_as_guest(self):
        """Should add a new vote for the specified release, which is given in the JSON."""
        response = self.app.post(
            "/api/1.0/votes/releases/",
            data=json.dumps(
                dict(
                    releaseID=self.release_ids[1],
                    rating=4,
                )
            ),
            content_type="application/json"
        )

        votes = VotesReleases.query.filter_by(ReleaseID=self.release_ids[1]).order_by(
            asc(VotesReleases.VoteID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.data.decode())
        self.assertEquals(2, len(votes))
        self.assertEquals(5.00, float(votes[0].Vote))
        self.assertEquals(4.00, float(votes[1].Vote))

    def test_adding_a_vote_as_registered_user(self):
        """Should add a new vote with the userID."""
        response = self.app.post(
            "/api/1.0/votes/releases/",
            data=json.dumps(
                dict(
                    releaseID=self.release_ids[1],
                    rating=3.5,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        votes = VotesReleases.query.filter_by(ReleaseID=self.release_ids[1]).order_by(
            asc(VotesReleases.VoteID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertEquals(2, len(votes))
        self.assertEquals(5.00, float(votes[0].Vote))
        self.assertEquals(3.50, float(votes[1].Vote))

    def test_adding_a_vote_as_registered_user_with_invalid_token(self):
        """Should throw a 401, since it is an invalid case."""
        response = self.app.post(
            "/api/1.0/votes/releases/",
            data=json.dumps(
                dict(
                    releaseID=self.release_ids[1],
                    rating=3.5,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": "not valid"
            }
        )

        votes = VotesReleases.query.filter_by(ReleaseID=self.release_ids[1]).order_by(
            asc(VotesReleases.VoteID)
        ).all()

        self.assertEquals(401, response.status_code)
        self.assertEquals(1, len(votes))
        self.assertEquals(5.00, float(votes[0].Vote))

    def test_adding_another_vote_as_registered_user_for_same_release(self):
        """Should replace the existing vote with the new one."""
        response = self.app.post(
            "/api/1.0/votes/releases/",
            data=json.dumps(
                dict(
                    releaseID=self.release_ids[2],
                    rating=3,
                )
            ),
            content_type="application/json",
            headers={
                "User": self.valid_reg_user,
                "Authorization": self.valid_token
            }
        )

        votes = VotesReleases.query.filter_by(ReleaseID=self.release_ids[2]).order_by(
            asc(VotesReleases.VoteID)
        ).all()

        votes_by_reg = VotesReleases.query.filter(
            VotesReleases.ReleaseID == self.release_ids[2],
            VotesReleases.UserID == self.valid_reg_user
        ).order_by(
            asc(VotesReleases.VoteID)
        ).all()

        self.assertEquals(201, response.status_code)
        self.assertEquals(3, len(votes))
        self.assertEquals(4.00, float(votes[0].Vote))
        self.assertEquals(1.00, float(votes[1].Vote))
        # This was originally 4.00 in setUp, and after the POST, should be 3.00
        self.assertEquals(3.00, float(votes[2].Vote))
        self.assertEquals(1, len(votes_by_reg))
