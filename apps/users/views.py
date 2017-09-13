import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from werkzeug.security import generate_password_hash

from app import db
from apps.users.models import Users
from apps.utils.time import get_datetime
from settings.config import CONFIG


class UsersView(FlaskView):
    """All things related to Users are handled here"""
    def index(self):
        """Return all users"""
        users = jsonify({
            "users": [{
                "id": user.UserID,
                "name": user.Name,
                "email": user.Email,
                "username": user.Username,
                "created": user.Created,
                "updated": user.Updated,
            } for user in Users.query.order_by(Users.UserID).all()]
        })
        return make_response(users, 200)

    def get(self, user_id):
        """Returns a specific user"""
        user = Users.query.filter_by(UserID=user_id).first_or_404()
        contents = jsonify({
            "users": [{
                "id": user.UserID,
                "name": user.Name,
                "email": user.Email,
                "username": user.Username,
                "created": user.Created,
                "updated": user.Updated,
            }]
        })
        return make_response(contents, 200)

    def post(self):
        """Add a new User. All new users start at normal level. Any promotions to eg. moderator,
        admin, or something else happens separately after the user is added. Passwords will be
        hashed with werkzeug. To compare the hashed pass, use:

            check_password_hash(database_value, "user input")

        which returns boolean"""
        data = json.loads(request.data.decode())
        if (
            not data["password"]
            or len(data["password"]) < CONFIG.MIN_PASSWORD_LENGTH
        ):
            result = {
                "success": False,
                "result": "Existing value is not identical to tested one"
            }
            return make_response(jsonify(result), 400)

        user = Users(
            Name=data["name"],
            Email=data["email"],
            Username=data["username"],
            Password=generate_password_hash(data["password"]),
            Created=get_datetime(),
        )
        db.session.add(user)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("UsersView:index"),
            user.UserID
        )
        return make_response(jsonify(contents), 201)
