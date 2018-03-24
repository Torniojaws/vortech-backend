import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc, func

from app import db, cache
from apps.releases.models import Releases
from apps.utils.time import get_datetime
from apps.votes.models import VotesReleases


class VotesView(FlaskView):
    """This is a bit special, since the base route will not really make sense for any situation.
    Instead, we'll have special routes for each type. Currently only Releases, though."""

    @route("/releases/", methods=["GET"])
    @cache.cached(timeout=60)
    def all_release_votes(self):
        """Return the votes for all releases. Release 1 first. If a release does not have votes,
        we return zeroes."""
        releases = Releases.query.order_by(asc(Releases.ReleaseID)).all()

        contents = jsonify({
            "votes": [{
                "releaseID": release.ReleaseID,
                "voteCount": self.get_vote_count(release.ReleaseID),
                "rating": self.get_rating(release.ReleaseID),
            } for release in releases]
        })

        return make_response(contents, 200)

    @route("/releases/<int:release_id>", methods=["GET"])
    @cache.cached(timeout=60)
    def release_votes(self, release_id):
        """Return the votes for a specific release."""
        contents = jsonify({
            "votes": [{
                "releaseID": release_id,
                "voteCount": self.get_vote_count(release_id),
                "rating": self.get_rating(release_id),
            }]
        })

        return make_response(contents, 200)

    @route("/releases/", methods=["POST"])
    def add_vote(self):
        """Add a vote to a release specified in the payload."""
        data = json.loads(request.data.decode())

        vote = VotesReleases(
            ReleaseID=data["releaseID"],
            Vote=data["rating"],
            Created=get_datetime(),
        )
        db.session.add(vote)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("VotesView:add_vote"),
            data["releaseID"]
        )

        return make_response(contents, 201)

    def get_vote_count(self, release_id):
        """Return the amount of votes the release has."""
        return VotesReleases.query.filter_by(ReleaseID=release_id).count()

    def get_rating(self, release_id):
        """Calculate the release rating to 2 decimals with: SUM(votes) / COUNT(votes)"""
        votes = VotesReleases.query.with_entities(
            func.sum(VotesReleases.Vote).label("sumVotes")
        ).filter_by(ReleaseID=release_id).first()

        voteCount = self.get_vote_count(release_id)
        rating = float(votes.sumVotes) / voteCount

        return round(rating, 2)
