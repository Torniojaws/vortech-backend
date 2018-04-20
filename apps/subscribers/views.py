"""Subscribers does not have a dedicated model. It uses the News and Users models."""

import json
import socket

from dictalchemy import make_class_dictable
from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import and_
from sqlalchemy.sql.expression import true

from app import db, cache
from apps.users.models import Users
from apps.users.views import get_user_level
from apps.utils.auth import registered_only, admin_only
from apps.utils.time import get_datetime

make_class_dictable(Users)


class SubscribersView(FlaskView):
    @admin_only
    @cache.cached(timeout=300)
    def index(self):
        """Return all valid (= has email) subscribers."""
        users = jsonify({
            "subscribers": [{
                "id": user.UserID,
                "name": user.Name,
                "email": user.Email,
                "username": user.Username,
                "level": get_user_level(user.UserID),
                "subscriber": user.Subscriber,
                "created": user.Created,
                "updated": user.Updated,
            } for user in Users.query.filter(
                and_(
                    Users.Subscriber == true(),
                    Users.Email.isnot(None)
                )
            ).order_by(Users.UserID).all()]
        })
        return make_response(users, 200)

    @registered_only
    @cache.cached(timeout=300)
    def get(self, user_id):
        """Returns a specific UserID data, IF he is a valid subscriber."""
        user = Users.query.filter(
            and_(
                Users.UserID == user_id,
                Users.Subscriber == true()
            )
        ).first_or_404()

        if not user.Email:
            contents = jsonify({
                "success": False,
                "message": "A valid email is required to subscribe"
            })
            return make_response(contents, 400)

        contents = jsonify({
            "subscribers": [{
                "id": user.UserID,
                "name": user.Name,
                "email": user.Email,
                "username": user.Username,
                "level": get_user_level(user.UserID),
                "subscriber": user.Subscriber,
                "created": user.Created,
                "updated": user.Updated,
            }]
        })
        return make_response(contents, 200)

    @registered_only
    def post(self):
        """Subscribes current UserID to updates."""
        data = json.loads(request.data.decode())
        user_id = int(request.headers.get("User", ""))
        user = Users.query.filter_by(UserID=user_id).first_or_404()

        if not user.Email:
            contents = jsonify({
                "success": False,
                "message": "A valid email is required to subscribe."
            })
            return make_response(contents, 400)

        if "subscribe" not in data:
            result = {
                "success": False,
                "result": "Subscribe flag missing from request"
            }
            return make_response(jsonify(result), 400)

        user.Subscriber = True
        user.Updated = get_datetime()
        # db.session.add(user)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("SubscribersView:index"),
            user.UserID
        )
        return make_response(jsonify(contents), 201)

    @registered_only
    def delete(self):
        """unsubscribe a user."""
        user_id = int(request.headers.get("User", ""))
        user = Users.query.filter_by(UserID=user_id).first_or_404()

        # It doesn't really matter if they have an email at this point
        # so let's just deactivate regardless
        user.Subscriber = False
        db.session.commit()

        return make_response("", 204)
