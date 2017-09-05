from flask_classful import FlaskView
from app import auto


class ApidocView(FlaskView):
    """The automatically generated API documentation is returned by this view."""
    def get(self):
        return auto.html()
