import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import and_, asc, desc
from dictalchemy import make_class_dictable

from app import db, cache
from apps.news.models import News, NewsCategoriesMapping, NewsCategories
from apps.news.patches import patch_item
from apps.utils.auth import admin_only
from apps.utils.strings import linux_linebreaks
from apps.utils.time import get_datetime, get_iso_format

make_class_dictable(News)
make_class_dictable(NewsCategoriesMapping)


class NewsView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all News items in reverse chronological order (newest first).
        When url parameters are given (usually for pagination), filter the query."""
        limit = request.args.get("limit", None)
        try:
            int(limit)
        except TypeError:
            limit = None
        first = request.args.get("first", None)
        try:
            int(first)
        except TypeError:
            first = None

        if limit is not None and first is not None:
            print("USING LIMIT AND FIRST")
            newsData = News.query.order_by(desc(News.Created)).offset(first).limit(limit).all()
        elif limit is not None:
            print("USING LIMIT ONLY")
            newsData = News.query.order_by(desc(News.Created)).limit(limit).all()
        else:
            print("GETTING ALL")
            newsData = News.query.order_by(desc(News.Created)).all()

        contents = jsonify({
            "news": [{
                "id": news.NewsID,
                "title": news.Title,
                "contents": linux_linebreaks(news.Contents),
                "author": news.Author,
                "created": get_iso_format(news.Created),
                "updated": get_iso_format(news.Updated),
                "categories": self.get_categories(news.NewsID),
            } for news in newsData]
        })
        return make_response(contents, 200)

    @cache.cached(timeout=300)
    def get(self, news_id):
        """Get a specific News item"""
        news = News.query.filter_by(NewsID=news_id).first_or_404()
        contents = jsonify({
            "news": [{
                "id": news.NewsID,
                "title": news.Title,
                "contents": linux_linebreaks(news.Contents),
                "author": news.Author,
                "created": get_iso_format(news.Created),
                "updated": get_iso_format(news.Updated),
                "categories": self.get_categories(news.NewsID),
            }]
        })
        return make_response(contents, 200)

    @admin_only
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

        # News items can have an existing category (=int), or a brand new one to be added
        # There is almost always more than one category for a news item
        for category in self.convert_categories(data["categories"]):
            if type(category) is not int:
                # Only add new category if it doesn't exist
                exists = NewsCategories.query.filter_by(Category=category).first()
                if not exists:
                    # New category, add it
                    cat = NewsCategories(
                        Category=category
                    )
                    db.session.add(cat)
                    db.session.commit()
                    category = cat.NewsCategoryID
                else:
                    # Reuse existing category
                    category = exists.NewsCategoryID

            # Map to the news
            # Don't map duplicate IDs, eg. when the same value or ID is twice in the request
            already_mapped = NewsCategoriesMapping.query.filter(
                and_(
                    NewsCategoriesMapping.NewsID == news_item.NewsID,
                    NewsCategoriesMapping.NewsCategoryID == category
                )
            ).first()

            if not already_mapped:
                cm = NewsCategoriesMapping(
                    NewsID=news_item.NewsID,
                    NewsCategoryID=category,
                )
                db.session.add(cm)
                db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("NewsView:index"),
            news_item.NewsID
        )
        return make_response(jsonify(contents), 201)

    @admin_only
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

        for category in self.convert_categories(data["categories"]):
            cm = NewsCategoriesMapping(
                NewsID=news_id,
                NewsCategoryID=category,
            )
            db.session.add(cm)
        db.session.commit()

        return make_response("", 200)

    @admin_only
    def patch(self, news_id):
        """Patch a given News item with RFC 6902 based partial updates."""
        data = json.loads(request.data.decode())
        result = patch_item(news_id, data)

        # On any exception, success is False.
        # Otherwise we return the result object, which has no success.
        if result.get("success", True):
            status_code = 200
        else:
            status_code = 422
            result = {"success": False, "message": "Could not apply patch"}

        return make_response(jsonify(result), status_code)

    @admin_only
    def delete(self, news_id):
        """Delete a News item"""
        news = News.query.filter_by(NewsID=news_id).first()
        db.session.delete(news)
        db.session.commit()

        return make_response("", 204)

    def get_categories(self, news_id):
        """Return a list of categories for the news_id"""
        mapped_ids = [
            m.NewsCategoryID for m in NewsCategoriesMapping.query.filter_by(NewsID=news_id).all()
        ]
        categories = NewsCategories.query.filter(
            NewsCategories.NewsCategoryID.in_(mapped_ids)
        ).all()
        return [c.Category for c in categories]

    def convert_categories(self, categories):
        """Make sure that the received categories are a valid list."""
        if type(categories) == str:
            categories = [cat.strip() for cat in categories.split(",")]

        result = []
        # Clean up the list. Numbers will be int(), empty values removed.
        for c in categories:
            try:
                current = int(c)
            except ValueError:
                if not c:
                    continue
                else:
                    current = c
            result.append(current)
        return result

    @route("/categories", methods=["GET"])
    @cache.cached(timeout=300)
    def news_categories(self):
        """Return all available News categories, eg. "Studio", "Recording", and their IDs."""
        contents = jsonify({
            "newsCategories": [{
                "id": category.NewsCategoryID,
                "category": category.Category
            } for category in NewsCategories.query.order_by(
                asc(NewsCategories.NewsCategoryID)).all()
            ]
        })
        return make_response(contents, 200)
