from apps.users.models import Users


def get_username(user_id):
    """Return the username of a given ID, or empty string if nothing found."""
    return Users.query.filter_by(UserID=user_id).first().Name
