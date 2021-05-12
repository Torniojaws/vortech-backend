"""Apply patches using the RFC 6902 format for patches."""

import json

from typing import List

from app import db

from apps.users.models import Users, UsersAccessMapping
from apps.utils.time import get_datetime
from settings.config import CONFIG
from werkzeug.security import check_password_hash, generate_password_hash


def patch_item(user_id, patches):
    user = Users.query.filter_by(UserID=user_id).first_or_404()
    result = {}

    if not isinstance(patches, List):
        patches = json.loads(patches)

    try:
        for patch in patches:
            apply_patch(user, patch, result)
    except AssertionError:
        db.session.rollback()
        return {"success": False, "message": "Test comparison did not match"}
    except ValueError:
        db.session.rollback()
        return {"success": False, "message": "The patch contained invalid operations"}

    return result


def apply_patch(user, patch, result):
    """Process a single patch, eg. {"op": "add", "path": "/username", "value": "Hi"}"""
    test_result = None

    if patch["op"] == "add":
        result = add(user, patch["path"], patch["value"], result)
    elif patch["op"] == "copy":
        result = copy(user, patch["from"], patch["path"], result)
    elif patch["op"] == "move":
        result = move(user, patch["from"], patch["path"], result)
    elif patch["op"] == "remove":
        result = remove(user, patch["path"], result)
    elif patch["op"] == "replace":
        result = replace(user, patch["path"], patch["value"], result)
    elif patch["op"] == "test":
        test_result = test(user, patch["path"], patch["value"])
        if test_result is False:
            raise AssertionError("Test operation did not pass - cancelling patch")
    else:
        raise ValueError("Unknown patch operation - cancelling patch and rolling back")

    # Do not update Users.Updated when a "test" op is run
    if not test_result:
        user.Updated = get_datetime()
    return result


def add(user, target, value, result):
    """Appends to array/object. In the case of string, replace the original."""
    if target == "/name":
        user.Name = value
        result["name"] = value
    elif target == "/email":
        user.Email = value
        result["email"] = value
    elif target == "/username":
        user.Username = value
        result["username"] = value
    elif target == "/password":
        if (
            not value
            or len(value) < CONFIG.MIN_PASSWORD_LENGTH
        ):
            raise ValueError("Password is too short! Must be at least {} characters.".format(
                CONFIG.MIN_PASSWORD_LENGTH)
            )
        user.Password = generate_password_hash(value)
        result["password"] = "The password has been updated"
    elif target == "/level":
        result["level"] = "User level is not allowed to be changed with PATCH"
    elif target == "/subscriber":
        user.Subscriber = value
        result["subscriber"] = value

    db.session.add(user)
    return result


def copy(user, source, target, result):
    user, result = update_values(user, source, target, result)
    db.session.add(user)
    return result


def move(user, source, target, result):
    """Makes target equal to source, and makes source null after that, if constraint allows."""
    if source == "/email":
        user, result = update_values(user, source, target, result)
        user.Email = None
    elif source == "/created":
        user, result = update_values(user, source, target, result)
        user.Created = None
    else:
        raise ValueError("Cannot move due to database constraints")

    db.session.add(user)
    return result


def remove(user, source, result):
    if source == "/email":
        user.Email = None
        result["email"] = None
    elif source == "/created":
        user.Created = None
        result["created"] = None
    elif source == "/updated":
        print("Will remove updated for userID = {}".format(user.UserID))
        user.Updated = None
        result["updated"] = None
    else:
        raise ValueError("Cannot remove due to database constraints")

    db.session.add(user)
    print("After remove, user.Updated == {}".format(user.Updated))
    return result


def replace(user, target, value, result):
    user, result = update_values(user, None, target, result, value)
    db.session.add(user)
    return result


def test(user, path, value):
    """Compare the value of "path" against "value"."""
    if path == "/name":
        return user.Name == value
    elif path == "/email":
        return user.Email == value
    elif path == "/username":
        return user.Username == value
    elif path == "/password":
        print("PSW on [{} {}]".format(
            type(value), value
        ))
        return check_password_hash(user.Password, value)
    elif path == "/level":
        return get_user_level(user.UserID) == value
    elif path == "/subscriber":
        return user.Subscriber == value
    elif path == "/created":
        return user.Created.strftime("%Y-%m-%d %H:%M:%S") == value
    elif path == "/updated":
        if user.Updated is None:
            return user.Updated == value
        else:
            return user.Updated.strftime("%Y-%m-%d %H:%M:%S") == value
    else:
        return False


def get_user_level(user_id):
    return UsersAccessMapping.query.filter_by(UserID=user_id).first_or_404().UsersAccessLevelID


def update_values(user, source, target, result, direct_value=None):
    if direct_value:
        value = direct_value
    else:
        value = get_value(user, source)

    if target == "/name":
        user.Name = value
        result["name"] = value
    elif target == "/email":
        user.Email = value
        result["email"] = value
    elif target == "/username":
        user.Username = value
        result["username"] = value
    elif target == "/password":
        user.Password = handle_password(user, value)
        result["password"] = "The password has been changed."
    elif target == "/level":
        result["level"] = "Changing user level is not allowed"
    elif target == "/subscriber":
        user.Subscriber = value
        result["subscriber"] = value
    elif target == "/created":
        result["created"] = "Changing the creation date is not allowed"
    elif target == "/updated":
        user.Updated = value
        result["updated"] = value
    else:
        raise ValueError("Unknown path given to operation!")

    return user, result


def handle_password(user, value):
    if not value or len(value) < CONFIG.MIN_PASSWORD_LENGTH:
        raise ValueError("Password is too short! Must be at least {} characters.".format(
            CONFIG.MIN_PASSWORD_LENGTH)
        )
    return generate_password_hash(value)


def get_value(user, source):
    """Read the value source has in the DB."""
    if source == "/name":
        return user.Name
    elif source == "/email":
        return user.Email
    elif source == "/username":
        return user.Username
    elif source == "/level":
        mapping = UsersAccessMapping.query.filter_by(UserID=user.UserID).first()
        return mapping.UsersAccessLevelID
    elif source == "/subscriber":
        return user.Subscriber
    elif source == "/created":
        return user.Created.strftime("%Y-%m-%d %H:%M:%S")
    elif source == "/updated":
        return user.Updated.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return ""
