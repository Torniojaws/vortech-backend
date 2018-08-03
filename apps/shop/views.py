import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc
from dictalchemy import make_class_dictable

from app import db, cache
from apps.shop.add_cu import add_categories, add_urls
from apps.shop.models import (
    ShopItems,
    ShopItemsCategoriesMapping,
    ShopItemsURLMapping,
    ShopCategories
)
from apps.shop.patches import patch_item
from apps.utils.auth import admin_only
from apps.utils.time import get_datetime

make_class_dictable(ShopItems)


class ShopItemsView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all shopitems ordered by ShopItemID, ID=1 first"""
        shopitems = ShopItems.query.order_by(asc(ShopItems.ShopItemID)).all()
        content = jsonify({
            "shopItems": [{
                "id": item.ShopItemID,
                "title": item.Title,
                "description": item.Description,
                "price": float(item.Price),
                "currency": item.Currency,
                "image": item.Image,
                "createdAt": item.Created,
                "updatedAt": item.Updated,
                "categories": self.get_categories(item.ShopItemID),
                "urls": self.get_urls(item.ShopItemID),
            } for item in shopitems]
        })

        return make_response(content, 200)

    @cache.cached(timeout=300)
    def get(self, item_id):
        """Return the details of the specified shop item."""
        item = ShopItems.query.filter_by(ShopItemID=item_id).first_or_404()
        content = jsonify({
            "shopItems": [{
                "id": item.ShopItemID,
                "title": item.Title,
                "description": item.Description,
                "price": float(item.Price),
                "currency": item.Currency,
                "image": item.Image,
                "createdAt": item.Created,
                "updatedAt": item.Updated,
                "categories": self.get_categories(item.ShopItemID),
                "urls": self.get_urls(item.ShopItemID),
            }]
        })

        return make_response(content, 200)

    @route("/category/<int:cat_id>/", methods=["GET"])
    @cache.cached(timeout=300)
    def category(self, cat_id):
        """Return all items that match the category ID."""
        matches = [
            mapping.ShopItemID for mapping in ShopItemsCategoriesMapping.query.filter_by(
                ShopCategoryID=cat_id
            ).all()
        ]
        shopitems = ShopItems.query.filter(
            ShopItems.ShopItemID.in_(matches)
        ).order_by(asc(ShopItems.ShopItemID)).all()
        content = jsonify({
            "shopItems": [{
                "id": item.ShopItemID,
                "title": item.Title,
                "description": item.Description,
                "price": float(item.Price),
                "currency": item.Currency,
                "image": item.Image,
                "createdAt": item.Created,
                "updatedAt": item.Updated,
                "categories": self.get_categories(item.ShopItemID),
                "urls": self.get_urls(item.ShopItemID),
            } for item in shopitems]
        })

        return make_response(content, 200)

    @admin_only
    def post(self):
        """Add a new Shop Item."""
        data = json.loads(request.data.decode())
        item = ShopItems(
            Title=data["title"],
            Description=data["description"],
            Price=data["price"],
            Currency=data["currency"],
            Image=data["image"],
            Created=get_datetime(),
        )
        db.session.add(item)
        db.session.commit()

        # After the item has been added, we can add the categories
        if "categories" in data:
            add_categories(item.ShopItemID, data["categories"])

        if "urls" in data:
            add_urls(item.ShopItemID, data["urls"])

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("ShopItemsView:index"),
            item.ShopItemID
        )

        return make_response(jsonify(contents), 201)

    @admin_only
    def put(self, item_id):
        """Overwrite all the data of the specified shop item."""
        data = json.loads(request.data.decode())
        item = ShopItems.query.filter_by(ShopItemID=item_id).first_or_404()

        # Update the Shop item
        item.Title = data["title"]
        item.Description = data["description"]
        item.Price = data["price"]
        item.Currency = data["currency"]
        item.Image = data["image"]
        item.Updated = get_datetime()

        # For the mappings, we delete all previous entries and insert the new ones
        for cat in ShopItemsCategoriesMapping.query.filter_by(ShopItemID=item_id).all():
            db.session.delete(cat)
        db.session.commit()

        for url in ShopItemsURLMapping.query.filter_by(ShopItemID=item_id).all():
            db.session.delete(url)
        db.session.commit()

        # Then add the new entries. Since it's a PUT, if no new values were provided, it is OK to
        # leave it empty for the current shop item.
        if "categories" in data:
            add_categories(item_id, data["categories"])

        if "urls" in data:
            add_urls(item_id, data["urls"])

        # Save all changes
        db.session.commit()

        return make_response("", 200)

    @admin_only
    def patch(self, item_id):
        """Partially modify the specified shopitem."""
        item = ShopItems.query.filter_by(ShopItemID=item_id).first_or_404()
        result = []
        status_code = 204

        # This only returns a value (boolean) for "op": "test"
        result = patch_item(item, request.get_json())

        return make_response(jsonify(result), status_code)

    @admin_only
    def delete(self, item_id):
        """Delete the specified item."""
        item = ShopItems.query.filter_by(ShopItemID=item_id).first_or_404()
        db.session.delete(item)
        db.session.commit()
        return make_response("", 204)

    def get_categories(self, item_id):
        """Return a list of category IDs for the current shopitem, in ascending order."""
        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=item_id).order_by(
            asc(ShopItemsCategoriesMapping.ShopCategoryID)
        ).all()
        return [c.ShopCategoryID for c in cats]

    def get_urls(self, item_id):
        """Return a list of dicts containing url mapping data for the current shopitem."""
        urls = ShopItemsURLMapping.query.filter_by(ShopItemID=item_id).order_by(
            asc(ShopItemsURLMapping.ShopItemsURLMappingID)
        ).all()

        result = []
        for url in urls:
            data = {
                "urlTitle": url.URLTitle,
                "url": url.URL,
                "logoID": url.ShopItemLogoID
            }
            result.append(data)

        return result

    @route("/categories", methods=["GET"])
    @cache.cached(timeout=300)
    def shop_categories(self):
        """Return all available Shop categories, eg. "Clothing", "Album", and their IDs."""
        contents = jsonify({
            "shopCategories": [{
                "id": category.ShopCategoryID,
                "category": category.Category,
                "subCategory": category.SubCategory
            } for category in ShopCategories.query.order_by(
                asc(ShopCategories.ShopCategoryID)).all()
            ]
        })
        return make_response(contents, 200)
