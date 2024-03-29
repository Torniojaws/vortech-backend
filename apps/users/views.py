import datetime
import json
import socket
import uuid

from dictalchemy import make_class_dictable
from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import and_, exc
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, cache
from apps.releases.models import Releases
from apps.users.models import Users, UsersAccessTokens, UsersAccessMapping
from apps.users.patches import patch_item
from apps.utils.auth import registered_only, admin_only
from apps.utils.time import get_datetime, get_datetime_one_hour_ahead
from apps.votes.models import VotesReleases
from settings.config import CONFIG

make_class_dictable(Users)


class UsersView(FlaskView):
    """All things related to Users are handled here"""
    @cache.cached(timeout=300)
    def index(self):
        """Return all users"""
        users = jsonify({
            "users": [{
                "id": user.UserID,
                "name": user.Name,
                "email": user.Email,
                "username": user.Username,
                "level": get_user_level(user.UserID),
                "subscriber": user.Subscriber,
                "created": user.Created,
                "updated": user.Updated,
            } for user in Users.query.order_by(Users.UserID).all()]
        })
        return make_response(users, 200)

    @registered_only
    @cache.cached(timeout=300)
    def get(self, user_id):
        """Returns a specific user"""
        user = Users.query.filter_by(UserID=user_id).first_or_404()
        contents = jsonify({
            "users": [{
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

    def post(self):
        """Add a new User. All new users start at normal level. Any promotions to eg. moderator,
        admin, or something else happens separately after the user is added. Passwords will be
        hashed with werkzeug. To compare the hashed pass, use:

            check_password_hash(database_value, "user input")

        which returns boolean"""
        data = json.loads(request.data.decode())

        if not data["name"] or not data["email"] or not data["username"]:
            return make_response(jsonify({
                "success": False,
                "result": "Validation failed",
                "errors": "Missing required data"
            }), 400)

        valid_password, result = validate_password(data)
        if not valid_password:
            return make_response(jsonify(result), 400)

        # Passed all checks, should be OK to add
        user = Users(
            Name=data["name"],
            Email=data["email"] or None,  # Empty strings would fail DB unique constraint
            Username=data["username"],
            Password=generate_password_hash(data["password"]),
            Created=get_datetime(),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except exc.IntegrityError as e:
            # The chance of duplicate users is low, so it is good enough to let it fail upon insert
            print(e)
            db.session.rollback()
            result = {
                "success": False,
                "result": "Display Name or Username is already in use."
            }
            return make_response(jsonify(result), 400)

        # Grant level 2 (= registered). Anything more is on a case-by-case basis.
        userlevel = UsersAccessMapping(
            UserID=user.UserID,
            UsersAccessLevelID=2
        )
        db.session.add(userlevel)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("UsersView:index"),
            user.UserID
        )
        return make_response(jsonify(contents), 201)

    @admin_only
    def put(self, user_id):
        """Update the data of a given user."""
        user = Users.query.filter_by(UserID=user_id).first_or_404()
        data = json.loads(request.data.decode())

        valid_password, result = validate_password(data)
        if not valid_password:
            return make_response(jsonify(result), 400)

        # Update the User
        user.Name = data["name"]
        user.Email = data["email"]
        user.Username = data["username"]
        user.Password = generate_password_hash(data["password"])
        user.Subscriber = data["subscriber"]
        user.Updated = get_datetime()

        db.session.commit()

        return make_response("", 200)

    @registered_only
    def patch(self, user_id):
        """Patch the user."""
        data = json.loads(request.data.decode())
        result = patch_item(user_id, data)

        # On any exception, success is False.
        # Otherwise we return the result object, which has no success.
        if result.get("success", True):
            status_code = 200
        else:
            status_code = 422
            result = {"success": False, "message": "Could not apply patch"}

        return make_response(jsonify(result), status_code)

    @registered_only
    def delete(self, user_id):
        """Delete the specified user."""
        user = Users.query.filter_by(UserID=user_id).first_or_404()
        db.session.delete(user)
        db.session.commit()
        return make_response("", 204)

    @registered_only
    @route("<int:user_id>/votes/releases/<int:release_id>", methods=["GET"])
    @cache.cached(timeout=300)
    def user_vote_on_release(self, user_id, release_id):
        """Return the vote the user has given to a Release."""
        release = Releases.query.filter_by(ReleaseID=release_id).first_or_404()
        vote = VotesReleases.query.filter(
            and_(
                VotesReleases.ReleaseID == release_id,
                VotesReleases.UserID == user_id
            )
        ).first_or_404()

        contents = jsonify({
            "voteID": vote.VoteID,
            "vote": float(vote.Vote),
            "releaseID": release.ReleaseID,
            "created_at": vote.Created,
            "updated_at": vote.Updated,
        })
        return make_response(contents, 200)


def get_user_level(user_id):
    """Get the given user's access level. This is used by the frontend to *display* the admin
    features (mostly forms in the profile page) if the UserID is an admin.

    If no mapping is found, we return the configured Guest Level (currently = 1).

    If someone modifies the localStorage level, they will see the admin features. But, the
    admin features have their own separate endpoint where the actual AccessToken and UserID
    are validated, so only "true admins" can actually do actions."""
    try:
        level = UsersAccessMapping.query.filter_by(UserID=user_id).first().UsersAccessLevelID
    except AttributeError:
        # No mapping found - use guest level
        level = CONFIG.GUEST_LEVEL
    return level


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
                ExpirationDate=get_datetime_one_hour_ahead(),
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


class UserRefreshTokenView(FlaskView):
    def post(self):
        """If the user's access token has expired, the frontend will attempt to send the refresh
        token to this endpoint. If the userID and refresh token are valid, we renew the access
        token to be valid for another hour."""
        user_id = request.headers.get("User", "")
        refresh_token = request.headers.get("Authorization", "")

        # Does UserID exist
        user_found = Users.query.filter_by(UserID=user_id).first()

        # Is refresh token valid for the user
        token_found = UsersAccessTokens.query.filter(
            and_(
                UsersAccessTokens.UserID == user_id,
                UsersAccessTokens.RefreshToken == refresh_token,
            )
        ).first()

        if user_found and token_found:
            # Then update the access token for the current valid login
            # NB: Refresh tokens never expire (standard practice), so don't create a new one.
            token_found.AccessToken = str(uuid.uuid4())
            token_found.ExpirationDate = get_datetime_one_hour_ahead()
            db.session.commit()

            status_code = 200
            result = {
                "success": True,
                "accessToken": token_found.AccessToken,
                "refreshToken": token_found.RefreshToken,
                "expires_in": 3600,
                "userID": user_id,
            }
        else:
            # UserID and/or refresh token was missing from headers.
            status_code = 404
            result = {
                "success": False,
                "error": "Missing UserID or valid Token"
            }

        return make_response(jsonify(result), status_code)


class UserLoginCheckView(FlaskView):
    def post(self):
        """Check the status of the User's tokens. When an access_token has expired, the user would
        send a refresh_token to generate a new valid access_token. The refresh_token does not
        expire."""
        try:
            data = json.loads(request.data.decode())
            user_id = data["id"]
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
        except ValueError:
            status_code = 400
            result = {
                "success": False,
                "error": "invalid_request"
            }
            return make_response(jsonify(result), status_code)
        except KeyError:
            status_code = 400
            result = {
                "success": False,
                "error": "invalid_request"
            }
            return make_response(jsonify(result), status_code)

        token = UsersAccessTokens.query.filter(and_(
            UsersAccessTokens.AccessToken == access_token,
            UsersAccessTokens.UserID == user_id,
        )).first()

        if not token or token.RefreshToken != refresh_token:
            status_code = 401
            result = {
                "success": False,
                "error": "invalid_token"
            }
            return make_response(jsonify(result), status_code)

        if token.ExpirationDate < datetime.datetime.now():
            # AccessToken has expired - generate a new AccessToken
            token.AccessToken = str(uuid.uuid4())
            token.ExpirationDate = get_datetime_one_hour_ahead()
            db.session.commit()

            status_code = 200
            result = {
                "success": True,
                "accessToken": token.AccessToken,
                "expires_in": 3600,
                "message": "AccessToken has been renewed"
            }
        else:
            status_code = 200
            result = {
                "success": True,
                "message": "AccessToken is valid"
            }

        return make_response(jsonify(result), status_code)


def validate_password(data):
    """This is used when adding or updating a user. In both cases, it is possible to update the
    user's password, so it must be checked."""
    if not data["password"]:
        result = {
            "success": False,
            "result": "Password missing."
        }
        return False, result

    if len(data["password"]) < CONFIG.MIN_PASSWORD_LENGTH:
        result = {
            "success": False,
            "result": "Password is too short. Minimum length is {} characters.".format(
                CONFIG.MIN_PASSWORD_LENGTH
            )
        }
        return False, result
    return True, None
