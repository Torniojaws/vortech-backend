from flask_classy import FlaskView, route


class UsersView(FlaskView):
    """All things related to Users are handled here"""
    @route("/", methods=["GET", "POST"])
    def index(self):
        return "Users!"
