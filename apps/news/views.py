from flask_classful import FlaskView, route

"""
Note to self:

For simple routes like
GET /news
POST /news
GET /news/:id
PATCH /news/:id
UPDATE /news/:id
DELETE /news/:id
Using the standard Flask-Classful methods is OK. Just needs a special handling for GET so that both
GET /news and GET /news/:id are supported.

For "special" cases like:
PATCH /news/:id:/comments/:id
It is fine to use the standard
@route("/<int:news_id>/comments/<int:comment_id>")
style
"""


class NewsView(FlaskView):
    def index(self):
        return "This is GET /news\n"

    def get(self, news_id):
        return "This is GET /news/{}\n".format(news_id)

    def post(self):
        return "This is GET /news\n"

    def put(self, news_id):
        return "This is PUT /news/{}\n".format(news_id)

    def patch(self, news_id):
        return "This is PATCH /news/{}\n".format(news_id)

    def delete(self, news_id):
        return "This is DELETE /news/{}\n".format(news_id)

    @route("/<int:news_id>/comments/<int:comment_id>", methods=["GET"])
    def news_comment(self, news_id, comment_id):
        return "This is GET /news/{}/comments/{}".format(news_id, comment_id)

    @route("/<int:news_id>/comments/", methods=["GET"])
    def news_comments(self, news_id):
        return "This is GET /news/{}/comments/".format(news_id)
