import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc
from dictalchemy import make_class_dictable

from app import db, cache
from apps.utils.time import get_datetime
from apps.photos.add_ac import add_album, add_categories
from apps.photos.models import (
    Photos, PhotosAlbumsMapping, PhotosCategoriesMapping, PhotoCategories
)
from apps.photos.patches import patch_item
from apps.utils.auth import admin_only

make_class_dictable(Photos)


class PhotosView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all photos in asc PhotoID order."""
        photos = Photos.query.order_by(asc(Photos.PhotoID)).all()
        content = jsonify({
            "photos": [{
                "id": photo.PhotoID,
                "image": photo.Image,
                "caption": photo.Caption,
                "takenBy": photo.TakenBy,
                "country": photo.Country,
                "countryCode": photo.CountryCode,
                "city": photo.City,
                "albumID": self.get_album_id(photo.PhotoID),
                "categories": self.get_categories(photo.PhotoID),
                "createdAt": photo.Created,
                "updatedAt": photo.Updated,
            } for photo in photos]
        })

        return make_response(content, 200)

    @cache.cached(timeout=300)
    def get(self, photo_id):
        """Return the details of the specified photo."""
        photo = Photos.query.filter_by(PhotoID=photo_id).first_or_404()
        content = jsonify({
            "photos": [{
                "id": photo.PhotoID,
                "image": photo.Image,
                "caption": photo.Caption,
                "takenBy": photo.TakenBy,
                "country": photo.Country,
                "countryCode": photo.CountryCode,
                "city": photo.City,
                "albumID": self.get_album_id(photo.PhotoID),
                "categories": self.get_categories(photo.PhotoID),
                "createdAt": photo.Created,
                "updatedAt": photo.Updated,
            }]
        })

        return make_response(content, 200)

    def albums(self, album_id):
        """Return all photos that are in a given photo album ID."""
        album_photos = PhotosAlbumsMapping.query.filter_by(AlbumID=album_id).order_by(
            asc(PhotosAlbumsMapping.PhotoID)
        ).all()
        album_photo_ids = [p.PhotoID for p in album_photos]
        photos = Photos.query.filter(Photos.PhotoID.in_(album_photo_ids)).all()

        content = jsonify({
            "photos": [{
                "id": photo.PhotoID,
                "image": photo.Image,
                "caption": photo.Caption,
                "takenBy": photo.TakenBy,
                "country": photo.Country,
                "countryCode": photo.CountryCode,
                "city": photo.City,
                "albumID": self.get_album_id(photo.PhotoID),
                "categories": self.get_categories(photo.PhotoID),
                "createdAt": photo.Created,
                "updatedAt": photo.Updated,
            } for photo in photos]
        })

        return make_response(content, 200)

    def categories(self, cat_id):
        """Return all photos that are in a given photo category."""
        cat_photos = PhotosCategoriesMapping.query.filter_by(PhotoCategoryID=cat_id).order_by(
            asc(PhotosCategoriesMapping.PhotoID)
        ).all()
        cat_photo_ids = [p.PhotoID for p in cat_photos]
        photos = Photos.query.filter(Photos.PhotoID.in_(cat_photo_ids)).all()

        content = jsonify({
            "photos": [{
                "id": photo.PhotoID,
                "image": photo.Image,
                "caption": photo.Caption,
                "takenBy": photo.TakenBy,
                "country": photo.Country,
                "countryCode": photo.CountryCode,
                "city": photo.City,
                "albumID": self.get_album_id(photo.PhotoID),
                "categories": self.get_categories(photo.PhotoID),
                "createdAt": photo.Created,
                "updatedAt": photo.Updated,
            } for photo in photos]
        })

        return make_response(content, 200)

    @admin_only
    def post(self):
        """Add a new Photo."""
        # TODO: Maybe allow adding multiple photos at once?
        data = json.loads(request.data.decode())
        photo = Photos(
            Image=data["image"],
            Caption=data["caption"],
            TakenBy=data["takenBy"],
            Country=data["country"],
            CountryCode=data["countryCode"],
            City=data["city"],
            Created=get_datetime()
        )
        db.session.add(photo)
        db.session.commit()

        # Add categories after the video has been inserted
        if "categories" in data:
            add_categories(photo.PhotoID, data["categories"])

        # Add album if provided (usually is)
        if "album" in data:
            add_album(photo.PhotoID, data["album"])

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("PhotosView:index"),
            photo.PhotoID
        )

        return make_response(jsonify(contents), 201)

    @admin_only
    def patch(self, photo_id):
        """Partially modify the specified photo."""
        photo = Photos.query.filter_by(PhotoID=photo_id).first_or_404()
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(photo, request.get_json())
            db.session.commit()
        except Exception as e:
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)

    @admin_only
    def delete(self, photo_id):
        """Delete the specified photo."""
        photo = Photos.query.filter_by(PhotoID=photo_id).first_or_404()
        db.session.delete(photo)
        db.session.commit()
        return make_response("", 204)

    def get_categories(self, photo_id):
        """Get the categories of the given photo."""
        categories = PhotosCategoriesMapping.query.filter_by(PhotoID=photo_id).order_by(
            asc(PhotosCategoriesMapping.PhotoCategoryID)
        ).all()
        return [c.PhotoCategoryID for c in categories]

    def get_album_id(self, photo_id):
        """Return the Album ID the Photo is in. If no album is assigned, return None."""
        return PhotosAlbumsMapping.query.filter_by(PhotoID=photo_id).first().AlbumID

    @route("/categories", methods=["GET"])
    @cache.cached(timeout=300)
    def photo_categories(self):
        """Return all available photo categories, eg. "Live", "Studio", and their IDs."""
        contents = jsonify({
            "photoCategories": [{
                "id": category.PhotoCategoryID,
                "category": category.Category
            } for category in PhotoCategories.query.order_by(
                asc(PhotoCategories.PhotoCategoryID)).all()
            ]
        })
        return make_response(contents, 200)
