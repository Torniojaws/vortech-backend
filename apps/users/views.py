from flask_classful import FlaskView


class UsersView(FlaskView):
    """All things related to Users are handled here"""
    def get(self):
        return "This is GET /users"

    def post(self):
        return "This is POST /users"
