from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import desc
import time

from app import db
from apps.news.models import News


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
        data = request.get_json()
        news_item = News(
            Title=data.title,
            Contents=data.contents,
            Author=data.author,
            Created=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(news_item)
        db.session.commit()
        content = "Location: {}{}".format(
            url_for("NewsView:index"),
            db.session.inserted_primary_key  # TODO: Does this work?
        )
        return make_response(jsonify(content), 201)

    def put(self, news_id):
        """Replace an existing News item with new data"""
        return "This is PUT /news/{}\n".format(news_id)

    def patch(self, news_id):
        """Change an existing News item partially"""
        return "This is PATCH /news/{}\n".format(news_id)

    def delete(self, news_id):
        """Delete a News item"""
        News.delete
        return "This is DELETE /news/{}\n".format(news_id)

    @route("/<int:news_id>/comments/<int:comment_id>", methods=["GET"])
    def news_comment(self, news_id, comment_id):
        """Return a specific comment to a given News item"""
        return "This is GET /news/{}/comments/{}\n".format(news_id, comment_id)

    @route("/<int:news_id>/comments/", methods=["GET"])
    def news_comments(self, news_id):
        """Return all comments for a given News item, in chronological order"""
        return "This is GET /news/{}/comments/\n".format(news_id)
