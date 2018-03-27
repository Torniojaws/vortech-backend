import json
import socket

from flask import abort, jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import asc, func, and_

from app import db, cache
from apps.photos.models import Photos
from apps.releases.models import Releases
from apps.utils.auth import validate_user
from apps.utils.time import get_datetime
from apps.votes.models import VotesReleases, VotesPhotos


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
        valid_user_id, registered, invalid_token = validate_user(request.headers)

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


class PhotosVotesView(FlaskView):
    @cache.cached(timeout=60)
    def index(self):
        """Return the votes for all photos. Photo 1 first. If a photo does not have votes,
        we return zeroes."""
        photos = Photos.query.order_by(asc(Photos.PhotoID)).all()

        contents = jsonify({
            "votes": [{
                "photoID": photo.PhotoID,
                "voteCount": self.get_vote_count(photo.PhotoID),
                "rating": self.get_rating(photo.PhotoID),
            } for photo in photos]
        })

        return make_response(contents, 200)

    @cache.cached(timeout=60)
    def get(self, photo_id):
        """Return the votes for a specific photo."""
        contents = jsonify({
            "votes": [{
                "photoID": int(photo_id),
                "voteCount": self.get_vote_count(photo_id),
                "rating": self.get_rating(photo_id),
            }]
        })

        return make_response(contents, 200)

    def post(self):
        """Add a vote to a photo specified in the payload."""
        data = json.loads(request.data.decode())
        valid_user_id, registered, invalid_token = validate_user(request.headers)

        existing_vote = None
        photo_id = int(data["photoID"])
        vote = data["rating"]

        if registered:
            if invalid_token:
                abort(401)
            else:
                # Check if the current registered user has already voted on the photo.
                existing_vote = VotesPhotos.query.filter(
                    and_(
                        VotesPhotos.PhotoID == photo_id,
                        VotesPhotos.UserID == valid_user_id
                    )
                ).first()

        if existing_vote:
            existing_vote.Vote = vote
            existing_vote.Updated = get_datetime()
        else:
            new_vote = VotesPhotos(
                PhotoID=photo_id,
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
            url_for("PhotosVotesView:index"),
            data["photoID"]
        )

        return make_response(contents, 201)

    def get_vote_count(self, photo_id):
        """Return the amount of votes the photo has."""
        return VotesPhotos.query.filter_by(PhotoID=photo_id).count()

    def get_rating(self, photo_id):
        """Calculate the photo rating to 2 decimals with: SUM(votes) / COUNT(votes)"""
        votes = VotesPhotos.query.with_entities(
            func.sum(VotesPhotos.Vote).label("sumVotes")
        ).filter_by(PhotoID=photo_id).first()

        voteCount = self.get_vote_count(photo_id)
        rating = float(votes.sumVotes) / voteCount

        return round(rating, 2)
