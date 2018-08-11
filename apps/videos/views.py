import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc, desc
from dictalchemy import make_class_dictable

from app import db, cache
from apps.utils.auth import admin_only
from apps.utils.time import get_datetime
from apps.videos.add_categories import add_categories
from apps.videos.models import Videos, VideosCategoriesMapping, VideoCategories
from apps.videos.patches import patch_item

make_class_dictable(Videos)


class VideosView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all videos in reverse chronological order."""
        videos = Videos.query.order_by(desc(Videos.VideoID)).all()
        content = jsonify({
            "videos": [{
                "title": video.Title,
                "url": video.URL,
                "createdAt": video.Created,
                "updatedAt": video.Updated,
                "categories": self.get_categories(video.VideoID),
            } for video in videos]
        })

        return make_response(content, 200)

    @cache.cached(timeout=300)
    def get(self, video_id):
        """Return the details of the specified video."""
        video = Videos.query.filter_by(VideoID=video_id).first_or_404()
        content = jsonify({
            "videos": [{
                "title": video.Title,
                "url": video.URL,
                "createdAt": video.Created,
                "updatedAt": video.Updated,
                "categories": self.get_categories(video.VideoID),
            }]
        })

        return make_response(content, 200)

    @admin_only
    def post(self):
        """Add a new Video."""
        # TODO: Maybe allow adding multiple videos at once?
        data = json.loads(request.data.decode())
        video = Videos(
            Title=data["title"],
            URL=data["url"],
            Created=get_datetime(),
        )
        db.session.add(video)
        db.session.commit()

        # Add categories after the video has been inserted
        if "categories" in data:
            add_categories(video.VideoID, data["categories"])

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("VideosView:index"),
            video.VideoID
        )

        return make_response(jsonify(contents), 201)

    @admin_only
    def put(self, video_id):
        """Overwrite all the data of the specified video."""
        data = json.loads(request.data.decode())
        video = Videos.query.filter_by(VideoID=video_id).first_or_404()

        # Update the Video
        video.Title = data["title"]
        video.URL = data["url"]
        video.Updated = get_datetime()

        # Remove the existing category mappings, before adding the new ones
        for cat in VideosCategoriesMapping.query.filter_by(VideoID=video_id).all():
            db.session.delete(cat)
        db.session.commit()

        # And then insert the new ones, if they were provided. If not, then the video will be
        # uncategorized. This is expected behaviour, as PUT is for replacing all data.
        if "categories" in data:
            add_categories(video_id, data["categories"])

        db.session.commit()

        return make_response("", 200)

    @admin_only
    def patch(self, video_id):
        """Partially modify the specified video."""
        video = Videos.query.filter_by(VideoID=video_id).first_or_404()
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(video, request.get_json())
            db.session.commit()
        except Exception as e:
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)

    @admin_only
    def delete(self, video_id):
        """Delete the specified video."""
        video = Videos.query.filter_by(VideoID=video_id).first_or_404()
        db.session.delete(video)
        db.session.commit()
        return make_response("", 204)

    def get_categories(self, video_id):
        """Get the categories of the given video."""
        categories = VideosCategoriesMapping.query.filter_by(VideoID=video_id).order_by(
            asc(VideosCategoriesMapping.VideoCategoryID)
        ).all()
        return [c.VideoCategoryID for c in categories]

    @route("/categories", methods=["GET"])
    @cache.cached(timeout=300)
    def video_categories(self):
        """Return all available Video categories, eg. "Live", "Studio", and their IDs."""
        contents = jsonify({
            "videoCategories": [{
                "id": category.VideoCategoryID,
                "category": category.Category
            } for category in VideoCategories.query.order_by(
                asc(VideoCategories.VideoCategoryID)).all()
            ]
        })
        return make_response(contents, 200)
