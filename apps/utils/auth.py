"""These two are used via decorators to validate the user is allowed to call the endpoint."""

from functools import wraps
from flask import abort, request
from datetime import datetime

from apps.users.models import UsersAccessTokens, UsersAccessMapping, Users
from settings.config import CONFIG


def invalid_token(user_id, access_token):
    """Check that user and user's token is valid."""
    token = UsersAccessTokens.query.filter_by(UserID=user_id).first()
    if token is None:
        return True
    if token.AccessToken != access_token:
        return True
    if token.ExpirationDate <= datetime.now():
        return True
    return False


def user_is_admin(user_id):
    """Check if the user is admin or not."""
    user = Users.query.filter_by(UserID=user_id).first()
    user_map = UsersAccessMapping.query.filter_by(UserID=user_id).first()
    if user is None:
        return False
    if user_map is None:
        return False
    if user_map.UsersAccessLevelID == CONFIG.ADMIN_LEVEL:
        return True
    return False


def user_is_registered_or_more(user_id):
    """Check that user is registered, moderator, or admin."""
    user = Users.query.filter_by(UserID=user_id).first()
    user_map = UsersAccessMapping.query.filter_by(UserID=user_id).first()
    if user is None:
        return False
    if user_map is None:
        return False
    if user_map.UsersAccessLevelID >= CONFIG.REGISTERED_LEVEL:
        return True
    return False


def admin_only(f):
    """When a route has this @admin_only decorator, that endpoint can only be accessed with a valid
    user_id and access_token provided in the request. Anything else will be a 401 Unauthorized."""
    @wraps(f)
    def check_user_level(*args, **kwargs):
        user_id = request.headers.get("User", "")
        access_token = request.headers.get("Authorization", "")

        if user_id and access_token:
            # Check that user is admin
            if user_is_admin(user_id) is False:
                abort(401)
            # And make sure the access token the user provided is still valid for that user
            if invalid_token(user_id, access_token):
                abort(401)
        else:
            abort(401)
        return f(*args, **kwargs)  # pragma: no cover
    return check_user_level


def registered_only(f):
    """When a route decorated with @registered_only is accessed, the user must be at least a valid
    Registered User level, or higher. Anything else will be a 401 Unauthorized."""
    @wraps(f)
    def check_user_level(*args, **kwargs):
        user_id = request.headers.get("User", "")
        access_token = request.headers.get("Authorization", "")

        if user_id and access_token:
            # Check that user is at least registered level. If less than that, respond with 401
            if user_is_registered_or_more(user_id) is False:
                abort(401)
            # And make sure the access token the user provided is still valid for that user
            if invalid_token(user_id, access_token):
                abort(401)
        else:
            abort(401)
        return f(*args, **kwargs)  # pragma: no cover
    return check_user_level


def user_id_or_guest(user_id):
    """Validate the input and return the userID, or the guest userID (= 1)"""
    try:
        valid_id = int(user_id)
    except (ValueError, TypeError):
        valid_id = 1
    if valid_id <= 0:
        valid_id = 1

    return valid_id


def validate_user(headers):
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
