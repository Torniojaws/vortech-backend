import json
import socket

from flask import abort, jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import asc, func, and_

from app import db, cache
from apps.releases.models import Releases
from apps.utils.auth import user_id_or_guest, invalid_token
from apps.utils.time import get_datetime
from apps.votes.models import VotesReleases


class ReleaseVotesView(FlaskView):
    @cache.cached(timeout=60)
    def index(self):
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

    @cache.cached(timeout=60)
    def get(self, release_id):
        """Return the votes for a specific release."""
        contents = jsonify({
            "votes": [{
                "releaseID": int(release_id),
                "voteCount": self.get_vote_count(release_id),
                "rating": self.get_rating(release_id),
            }]
        })

        return make_response(contents, 200)

    def post(self):
        """Add a vote to a release specified in the payload."""
        data = json.loads(request.data.decode())
        valid_user_id, registered, invalid_token = self.validate_user(request.headers)

        existing_vote = None
        release_id = int(data["releaseID"])
        vote = data["rating"]

        if registered:
            if invalid_token:
                abort(401)
            else:
                # Check if the current registered user has already voted on the release.
                existing_vote = VotesReleases.query.filter(
                    and_(
                        VotesReleases.ReleaseID == release_id,
                        VotesReleases.UserID == valid_user_id
                    )
                ).first()

        if existing_vote:
            existing_vote.Vote = vote
            existing_vote.Updated = get_datetime()
        else:
            new_vote = VotesReleases(
                ReleaseID=release_id,
                Vote=vote,
                UserID=valid_user_id,
                Created=get_datetime(),
            )
            db.session.add(new_vote)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("ReleaseVotesView:index"),
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

    def validate_user(self, headers):
        """Validate the user and return the results."""
        user_id = headers.get("User", "")
        token = headers.get("Authorization", "")
        registered = False

        if user_id:
            valid_user_id = user_id_or_guest(user_id)
            registered = valid_user_id > 1
        else:
            valid_user_id = 1

        is_token_invalid = invalid_token(user_id, token)

        return valid_user_id, registered, is_token_invalid
