import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import asc
from dictalchemy import make_class_dictable

from app import db
from apps.shop.models import ShopItems, ShopItemsCategoriesMapping, ShopItemsURLMapping
from apps.shop.patches import patch_item

make_class_dictable(ShopItems)


class ShopItemsView(FlaskView):
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

    def post(self):
        """Add a new Shop Item."""
        data = json.loads(request.data.decode())
        item = ShopItems(
            Title=data["title"],
            Duration=data["duration"],
        )
        db.session.add(item)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("ShopItemsView:index"),
            item.ShopItemID
        )

        return make_response(jsonify(contents), 201)

    def put(self, item_id):
        """Overwrite all the data of the specified shop item."""
        data = json.loads(request.data.decode())
        item = ShopItems.query.filter_by(ShopItemID=item_id).first_or_404()

        # Update the Song
        item.Title = data["title"]
        item.Duration = data["duration"]

        db.session.commit()

        return make_response("", 200)

    def patch(self, item_id):
        """Partially modify the specified shopitem."""
        item = ShopItems.query.filter_by(ShopItemID=item_id).first_or_404()
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(item, request.get_json())
            db.session.commit()
        except Exception as e:
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)

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
