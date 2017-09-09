from copy import deepcopy
import json
import socket
import time

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from jsonpatch import JsonPatch, JsonPatchTestFailed
from sqlalchemy import desc
from dictalchemy import make_class_dictable

from app import db
from apps.news.models import News
make_class_dictable(News)


class NewsView(FlaskView):
    def index(self):
        """Return all News items in reverse chronological order (newest first)"""
        contents = jsonify({
            "news": [{
                "id": news.NewsID,
                "title": news.Title,
                "contents": news.Contents,
                "author": news.Author,
                "created": news.Created,
                "updated": news.Updated,
            } for news in News.query.order_by(desc(News.Created)).all()]
        })
        return make_response(contents, 200)

    def get(self, news_id):
        """Get a specific News item"""
        news = News.query.filter_by(NewsID=news_id).first_or_404()
        contents = jsonify({
            "news": [{
                "id": news.NewsID,
                "title": news.Title,
                "contents": news.Contents,
                "author": news.Author,
                "created": news.Created,
                "updated": news.Updated,
            }]
        })
        return make_response(contents, 200)

    def post(self):
        """Add a new News item"""
        data = json.loads(request.data.decode())
        news_item = News(
            Title=data["title"],
            Contents=data["contents"],
            Author=data["author"],
            Created=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(news_item)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("NewsView:index"),
            news_item.NewsID
        )
        return make_response(jsonify(contents), 201)

    def put(self, news_id):
        """Replace an existing News item with new data"""
        data = json.loads(request.data.decode())
        news = News.query.get_or_404(news_id)

        # Update the news item
        news.Title = data["title"]
        news.Contents = data["contents"]
        news.Author = data["author"]
        news.Updated = time.strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

        return make_response("", 200)

    def patch(self, news_id):
        """Change an existing News item partially using an instruction-based JSON, as defined by:
        https://tools.ietf.org/html/rfc6902
        """
        news_item = News.query.get_or_404(news_id)
        result = None
        try:
            self.patch_item(news_item, request.get_json())
            db.session.commit()
            result = news_item.asdict()
        except JsonPatchTestFailed:
            # This is raised when using "op": "test" and the compared values are not identical
            result = {"success": False, "result": "Existing value is not identical to tested one"}

        return make_response(jsonify(result), 200)

    def delete(self, news_id):
        """Delete a News item"""
        news = News.query.filter_by(NewsID=news_id).first()
        db.session.delete(news)
        db.session.commit()

        return make_response("", 204)

    @route("/<int:news_id>/comments/<int:comment_id>", methods=["GET"])
    def news_comment(self, news_id, comment_id):
        """Return a specific comment to a given News item"""
        return "This is GET /news/{}/comments/{}\n".format(news_id, comment_id)

    @route("/<int:news_id>/comments/", methods=["GET"])
    def news_comments(self, news_id):
        """Return all comments for a given News item, in chronological order"""
        return "This is GET /news/{}/comments/\n".format(news_id)

    def patch_item(self, news, patchdata, **kwargs):
        """This is used to run patches on the database model, using the method described here:
        https://gist.github.com/mattupstate/d63caa0156b3d2bdfcdb
        """
        # Map the values to DB column names
        mapped_patchdata = []
        for p in patchdata:
            # Replace eg. /title with /Title
            p = self.patch_mapping(p)
            mapped_patchdata.append(p)

        data = news.asdict(exclude_pk=True, **kwargs)
        patch = JsonPatch(mapped_patchdata)
        data = patch.apply(data)
        news.fromdict(data)

    def patch_mapping(self, patch):
        """This is used to map a patch "path" or "from" to a custom value.
        Useful for when the patch path/from is not the same as the DB column name.

        Eg.
        PATCH /news/123
        [{ "op": "move", "from": "/title", "path": "/author" }]

        If the News column is "Title", having "/title" would fail to patch because the case does
        not match. So the mapping converts this:
            { "op": "move", "from": "/title", "path": "/author" }
        To this:
            { "op": "move", "from": "/Title", "path": "/Author" }
        """
        mapping = {
            "/title": "/Title",
            "/contents": "/Contents",
            "/author": "/Author",
            "/updated": "/Updated"
        }

        mutable = deepcopy(patch)
        for prop in patch:
            if prop == "path" or prop == "from":
                mutable[prop] = mapping.get(patch[prop], None)
        return mutable
