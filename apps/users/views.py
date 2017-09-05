from flask_classful import FlaskView


class UsersView(FlaskView):
    """All things related to Users are handled here"""
    def get(self):
        """Returns all Users"""
        return "This is GET /users"

    def post(self):
        """Add a new User"""
        return "This is POST /users"
