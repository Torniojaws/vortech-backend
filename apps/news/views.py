from flask_classful import FlaskView


class NewsView(FlaskView):
    def index(self):
        return "News index"

    def get(self, news_id):
        if news_id:
            return "This is GET /news/{}".format(news_id)
        else:
            return "This is GET /news"

    def post(self):
        return "This is POST /news"


"""
TODO:
/api/1.0/news/123/comments/321

Seems to be like this:
NewsView():
    def something():


# SOmething like this in https://pythonhosted.org/Flask-Classful/
class AnotherView(FlaskView):
    route_base = "home"

    def this_view(self, arg1, arg2):
        return "Args: %s, %s" % (arg1, arg2,)
"""
