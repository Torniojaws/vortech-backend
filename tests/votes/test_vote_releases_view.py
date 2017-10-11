import json
import unittest
from sqlalchemy import asc

from app import app, db
from apps.releases.models import Releases
from apps.votes.models import VotesReleases
from apps.utils.time import get_datetime


class TestVoteReleasesView(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # Add three releases
        release1 = Releases(
            Title="UnitTest 1",
            Date=get_datetime(),
            Artist="UnitTest Arts 1",
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
        release3 = Releases(
            Title="UnitTest 3",
            Date=get_datetime(),
            Artist="UnitTest 3 Arts",
            Credits="UnitTest three's a crowd",
            Created=get_datetime(),
        )
        db.session.add(release1)
        db.session.add(release2)
        db.session.add(release3)
        db.session.commit()

        self.release_ids = [release1.ReleaseID, release2.ReleaseID, release3.ReleaseID]

        # Add some votes for each release - minimum is 1.0, maximum is 5.0. The real steps will be
        # in 0.5 increments. However, any 2 decimal float between 1.00 and 5.00 is technically ok.
        rel1_vote1 = VotesReleases(ReleaseID=self.release_ids[0], Vote=4, Created=get_datetime())
        rel1_vote2 = VotesReleases(ReleaseID=self.release_ids[0], Vote=3.0, Created=get_datetime())
        rel1_vote3 = VotesReleases(ReleaseID=self.release_ids[0], Vote=3.00, Created=get_datetime())

        rel2_vote1 = VotesReleases(ReleaseID=self.release_ids[1], Vote=5, Created=get_datetime())

        rel3_vote1 = VotesReleases(ReleaseID=self.release_ids[2], Vote=4, Created=get_datetime())
        rel3_vote2 = VotesReleases(ReleaseID=self.release_ids[2], Vote=1, Created=get_datetime())

        db.session.add(rel1_vote1)
        db.session.add(rel1_vote2)
        db.session.add(rel1_vote3)
        db.session.add(rel2_vote1)
        db.session.add(rel3_vote1)
        db.session.add(rel3_vote2)
        db.session.commit()

    def tearDown(self):
        # Deleting a release will also delete the votes for it
        for release in Releases.query.filter(Releases.Title.like("UnitTest%")).all():
            db.session.delete(release)
        db.session.commit()

    def test_getting_all_votes(self):
        """Should return the current votes for all releases."""
        response = self.app.get("/api/1.0/votes/releases/")
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(3, len(data["votes"]))
        self.assertEquals(self.release_ids[0], data["votes"][0]["releaseID"])
        self.assertEquals(3, data["votes"][0]["voteCount"])
        self.assertEquals(3.33, data["votes"][0]["rating"])

        self.assertEquals(self.release_ids[2], data["votes"][2]["releaseID"])
        self.assertEquals(2, data["votes"][2]["voteCount"])
        self.assertEquals(2.50, data["votes"][2]["rating"])

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

    def test_adding_a_vote(self):
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
