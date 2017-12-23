import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc, desc
from dictalchemy import make_class_dictable

from app import db
from apps.news.models import News, NewsComments, NewsCategoriesMapping, NewsCategories
from apps.news.patches import patch_item
from apps.utils.time import get_datetime, get_iso_format

make_class_dictable(News)
make_class_dictable(NewsCategoriesMapping)


class NewsView(FlaskView):
    def index(self):
        """Return all News items in reverse chronological order (newest first)"""
        contents = jsonify({
            "news": [{
                "id": news.NewsID,
                "title": news.Title,
                "contents": news.Contents,
                "author": news.Author,
                "created": get_iso_format(news.Created),
                "updated": get_iso_format(news.Updated),
                "categories": self.get_categories(news.NewsID),
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
                "created": get_iso_format(news.Created),
                "updated": get_iso_format(news.Updated),
                "categories": self.get_categories(news.NewsID),
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
            Created=get_datetime(),
        )
        db.session.add(news_item)
        # Flush so that we can use the insert ID for the categories
        db.session.flush()

        # There is almost always more than one category for a news item
        for category in data["categories"]:
            cm = NewsCategoriesMapping(
                NewsID=news_item.NewsID,
                NewsCategoryID=category,
            )
            db.session.add(cm)

        # Finally, commit all the inserts above
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
        news.Updated = get_datetime()

        # Update Categories. Since they are one per row, we'll just delete and add.
        db.session.query(NewsCategoriesMapping).filter_by(NewsID=news_id).delete()
        db.session.commit()

        for category in data["categories"]:
            cm = NewsCategoriesMapping(
                NewsID=news_id,
                NewsCategoryID=category,
            )
            db.session.add(cm)
        db.session.commit()

        return make_response("", 200)

    def patch(self, news_id):
        """Change an existing News item partially using an instruction-based JSON, as defined by:
        https://tools.ietf.org/html/rfc6902

        When patching a joined table (like NewsCategoriesMapping), it should behave like a partial
        PUT, so basically just a delete+add instead of nothing fancy.

        According to RFC 5789, a PATCH should generally return 204 No Content, unless there were
        errors. We return 422 Unprocessable Entity if the patch JSON is ok, but could
        not be completed.
        """
        news_item = News.query.get_or_404(news_id)
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(news_item, request.get_json())
            db.session.commit()
        except Exception as e:
            print("News Patch threw error:")
            print(e)
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)

    def delete(self, news_id):
        """Delete a News item"""
        news = News.query.filter_by(NewsID=news_id).first()
        db.session.delete(news)
        db.session.commit()

        return make_response("", 204)

    @route("/<int:news_id>/comments/<int:comment_id>", methods=["GET"])
    def news_comment(self, news_id, comment_id):
        """Return a specific comment to a given News item"""
        comment = NewsComments.query.filter_by(
            NewsID=news_id,
            NewsCommentID=comment_id
        ).first_or_404()

        contents = jsonify({
            "comments": [{
                "id": comment.NewsCommentID,
                "newsId": comment.NewsID,
                "userId": comment.UserID,
                "comment": comment.Comment,
                "created": comment.Created,
                "updated": comment.Updated,
            }]
        })
        return make_response(contents, 200)

    @route("/<int:news_id>/comments/", methods=["GET"])
    def news_comments(self, news_id):
        """Return all comments for a given News item, in chronological order"""
        comments = NewsComments.query.filter_by(NewsID=news_id).order_by(
            asc(NewsComments.Created)
        ).all()

        contents = jsonify({
            "comments": [{
                "id": comment.NewsCommentID,
                "newsId": comment.NewsID,
                "userId": comment.UserID,
                "comment": comment.Comment,
                "created": comment.Created,
                "updated": comment.Updated,
            } for comment in comments]
        })
        return make_response(contents, 200)

    def get_categories(self, news_id):
        """Return a list of categories for the news_id"""
        mapped_ids = [
            m.NewsCategoryID for m in NewsCategoriesMapping.query.filter_by(NewsID=news_id).all()
        ]
        categories = NewsCategories.query.filter(
            NewsCategories.NewsCategoryID.in_(mapped_ids)
        ).all()
        return [c.NewsCategory for c in categories]
