from flask_classful import FlaskView

from app import auto


class UsersView(FlaskView):
    """All things related to Users are handled here"""
    @auto.doc()
    def get(self):
        """Returns all Users"""
        return "This is GET /users"

    @auto.doc()
    def post(self):
        """Add a new User"""
        return "This is POST /users"
