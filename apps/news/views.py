from flask_classful import FlaskView, route


class NewsView(FlaskView):
    def index(self):
        return "This is GET /news\n"

    def get(self, news_id):
        return "This is GET /news/{}\n".format(news_id)

    def post(self):
        return "This is POST /news\n"

    def put(self, news_id):
        return "This is PUT /news/{}\n".format(news_id)

    def patch(self, news_id):
        return "This is PATCH /news/{}\n".format(news_id)

    def delete(self, news_id):
        return "This is DELETE /news/{}\n".format(news_id)

    @route("/<int:news_id>/comments/<int:comment_id>", methods=["GET"])
    def news_comment(self, news_id, comment_id):
        return "This is GET /news/{}/comments/{}\n".format(news_id, comment_id)

    @route("/<int:news_id>/comments/", methods=["GET"])
    def news_comments(self, news_id):
        return "This is GET /news/{}/comments/\n".format(news_id)
