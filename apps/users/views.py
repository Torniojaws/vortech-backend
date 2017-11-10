import json
import socket
import uuid

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from apps.users.models import Users, UsersAccessTokens
from apps.utils.auth import registered_only
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

    @registered_only
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
                "result": "Password is missing or too short."
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


class UserLoginView(FlaskView):
    def post(self):
        """Compare username and matching hashed password to user input. If valid, generate the
        access token and return the details. The frontend will then update the session."""
        data = json.loads(request.data.decode())

        # Check that user exists
        user = Users.query.filter_by(Username=data["username"]).first_or_404()

        # If so, then compare the given password to the password of the matching user
        if check_password_hash(user.Password, data["password"]):
            # If there are existing access tokens for current user, remove them first
            for old_token in UsersAccessTokens.query.filter_by(UserID=user.UserID).all():
                db.session.delete(old_token)
                db.session.commit()

            # Then create the token for the current valid login
            token = UsersAccessTokens(
                UserID=user.UserID,
                AccessToken=str(uuid.uuid4()),
                RefreshToken=str(uuid.uuid4()),
                ExpirationDate=get_datetime(),
            )
            db.session.add(token)
            db.session.commit()

            status_code = 201
            result = {
                "success": True,
                "accessToken": token.AccessToken,
                "refreshToken": token.RefreshToken,
                "expires_in": 3600,
                "userID": user.UserID,
            }
        else:
            # Invalid password
            status_code = 401
            result = {
                "success": False,
                "error": "Invalid password."
            }

        return make_response(jsonify(result), status_code)


class UserLogoutView(FlaskView):
    def post(self):
        """Logout user - delete the UsersAccessToken(s) for current UserID."""
        user_id = request.headers.get("User", "")
        access_token = request.headers.get("Authorization", "")

        # Does UserID exist
        user_found = Users.query.filter_by(UserID=user_id).first()

        # The access token is just a formality, since this will revoke all access anyway.
        if user_found and access_token:
            # Delete the token(s) - after this point, even valid requests will not pass
            for token in UsersAccessTokens.query.filter_by(UserID=user_id).all():
                db.session.delete(token)
                db.session.commit()
            status_code = 200
            result = {
                "success": True
            }
        else:
            # UserID and/or AccessToken was missing from headers - do not logout
            status_code = 404
            result = {
                "success": False,
                "error": "Missing UserID or Token"
            }

        return make_response(jsonify(result), status_code)
