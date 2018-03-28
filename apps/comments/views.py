import json
import socket

from flask import abort, jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import asc

from app import db, cache
from apps.comments.models import CommentsNews, CommentsReleases
from apps.utils.auth import registered_only
from apps.utils.users import get_username
from apps.utils.time import get_datetime, get_iso_format


class NewsCommentsView(FlaskView):
    @cache.cached(timeout=60)
    def index(self):
        """Return all comments for all news."""
        comments = CommentsNews.query.order_by(
            asc(CommentsNews.NewsID),
            asc(CommentsNews.Created)
        ).all()

        contents = jsonify({
            "comments": [{
                "commentID": comment.CommentID,
                "newsID": comment.NewsID,
                "userID": comment.UserID,
                "name": get_username(comment.UserID),
                "comment": comment.Comment,
                "createdAt": get_iso_format(comment.Created),
                "updatedAt": get_iso_format(comment.Updated),
            } for comment in comments]
        })

        return make_response(contents, 200)

    @cache.cached(timeout=60)
    def get(self, news_id):
        """Return the comments for a specific news."""
        comments = CommentsNews.query.filter_by(NewsID=news_id).order_by(
            asc(CommentsNews.Created)
        ).all()

        contents = jsonify({
            "comments": [{
                "commentID": comment.CommentID,
                "newsID": comment.NewsID,
                "userID": comment.UserID,
                "name": get_username(comment.UserID),
                "comment": comment.Comment,
                "createdAt": get_iso_format(comment.Created),
                "updatedAt": get_iso_format(comment.Updated),
            } for comment in comments]
        })

        return make_response(contents, 200)

    @registered_only
    def post(self):
        """Add a comment to a news specified in the payload."""
        data = json.loads(request.data.decode())

        new_comment = CommentsNews(
            NewsID=int(data["newsID"]),
            Comment=data["comment"],
            UserID=int(request.headers.get("User", "")),
            Created=get_datetime(),
        )
        db.session.add(new_comment)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("NewsCommentsView:index"),
            data["newsID"]
        )

        return make_response(contents, 201)

    @registered_only
    def put(self, news_id):
        """Edit a comment. Verify that UserID matches original, otherwise 401."""
        data = json.loads(request.data.decode())

        comment_id = data.get("commentID", "")
        comment = data.get("comment", "")
        user_id = int(request.headers.get("User", ""))

        if not comment_id or not comment:
            abort(400)

        original_comment = CommentsNews.query.filter_by(CommentID=comment_id).first_or_404()
        if user_id == original_comment.UserID:
            # All OK, we can update the comment
            original_comment.Comment = comment
            original_comment.Updatd = get_datetime()
            db.session.commit()
        else:
            abort(401)

        return make_response("", 200)

    @registered_only
    def delete(self, news_id):
        """Delete a comment. This is kinda hairy in regards to idempotency."""
        data = json.loads(request.data.decode())

        comment_id = data.get("commentID", "")
        user_id = int(request.headers.get("User", ""))

        if not comment_id:
            abort(400)

        comment = CommentsNews.query.filter_by(CommentID=comment_id).first_or_404()
        if user_id == comment.UserID:
            # All OK, we can delete the comment
            db.session.delete(comment)
            db.session.commit()
        else:
            abort(401)

        return make_response("", 204)


class ReleaseCommentsView(FlaskView):
    @cache.cached(timeout=60)
    def index(self):
        """Return all comments for all releases."""
        comments = CommentsReleases.query.order_by(
            asc(CommentsReleases.ReleaseID),
            asc(CommentsReleases.Created)
        ).all()

        contents = jsonify({
            "comments": [{
                "commentID": comment.CommentID,
                "releaseID": comment.ReleaseID,
                "userID": comment.UserID,
                "name": get_username(comment.UserID),
                "comment": comment.Comment,
                "createdAt": get_iso_format(comment.Created),
                "updatedAt": get_iso_format(comment.Updated),
            } for comment in comments]
        })

        return make_response(contents, 200)

    @cache.cached(timeout=60)
    def get(self, release_id):
        """Return the comments for a specific release."""
        comments = CommentsReleases.query.filter_by(ReleaseID=release_id).order_by(
            asc(CommentsReleases.Created)
        ).all()

        contents = jsonify({
            "comments": [{
                "commentID": comment.CommentID,
                "releaseID": comment.ReleaseID,
                "userID": comment.UserID,
                "name": get_username(comment.UserID),
                "comment": comment.Comment,
                "createdAt": get_iso_format(comment.Created),
                "updatedAt": get_iso_format(comment.Updated),
            } for comment in comments]
        })

        return make_response(contents, 200)

    @registered_only
    def post(self):
        """Add a comment to a release specified in the payload."""
        data = json.loads(request.data.decode())

        new_comment = CommentsReleases(
            ReleaseID=int(data["releaseID"]),
            Comment=data["comment"],
            UserID=int(request.headers.get("User", "")),
            Created=get_datetime(),
        )
        db.session.add(new_comment)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("ReleaseCommentsView:index"),
            data["releaseID"]
        )

        return make_response(contents, 201)

    @registered_only
    def put(self, release_id):
        """Edit a comment. Verify that UserID matches original, otherwise 401."""
        data = json.loads(request.data.decode())

        comment_id = data.get("commentID", "")
        comment = data.get("comment", "")
        user_id = int(request.headers.get("User", ""))

        if not comment_id or not comment:
            abort(400)

        original_comment = CommentsReleases.query.filter_by(CommentID=comment_id).first_or_404()
        if user_id == original_comment.UserID:
            # All OK, we can update the comment
            original_comment.Comment = comment
            original_comment.Updatd = get_datetime()
            db.session.commit()
        else:
            abort(401)

        return make_response("", 200)

    @registered_only
    def delete(self, release_id):
        """Delete a comment. This is kinda hairy in regards to idempotency."""
        data = json.loads(request.data.decode())

        comment_id = data.get("commentID", "")
        user_id = int(request.headers.get("User", ""))

        if not comment_id:
            abort(400)

        comment = CommentsReleases.query.filter_by(CommentID=comment_id).first_or_404()
        if user_id == comment.UserID:
            # All OK, we can delete the comment
            db.session.delete(comment)
            db.session.commit()
        else:
            abort(401)

        return make_response("", 204)
