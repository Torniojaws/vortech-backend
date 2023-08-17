import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import desc
from dictalchemy import make_class_dictable

from app import db, cache
from apps.guestbook.models import Guestbook
from apps.guestbook.patches import patch_item
from apps.users.models import Users
from apps.utils.auth import admin_only
from apps.utils.strings import int_or_none
from apps.utils.time import get_datetime

make_class_dictable(Guestbook)


class GuestbookView(FlaskView):
    # @cache.cached(timeout=60) Disabled for now, for better UX until Redis can handle updates
    def index(self):
        """Return all guestbook posts ordered by GuestbookID in reverse chronological order.
        When url parameters are given (usually for pagination), filter the query."""
        limit = int_or_none(request.args.get("limit", None))
        first = int_or_none(request.args.get("first", None))

        if limit is not None and first is not None:
            guestbookData = Guestbook.query.order_by(
                desc(Guestbook.GuestbookID)
            ).offset(first).limit(limit).all()
        elif limit is not None:
            guestbookData = Guestbook.query.order_by(
                desc(Guestbook.GuestbookID)
            ).limit(limit).all()
        else:
            guestbookData = Guestbook.query.order_by(desc(Guestbook.GuestbookID)).all()

        content = jsonify({
            "guestbook": [{
                "id": book.GuestbookID,
                "name": book.Author,
                "message": book.Message,
                "isGuest": book.UserID == 1,
                "adminComment": book.AdminComment,
                "createdAt": book.Created,
                "updatedAt": book.Updated,
            } for book in guestbookData]
        })

        return make_response(content, 200)

    @cache.cached(timeout=60)
    def get(self, book_id):
        """Return a specific guestbook post."""
        book = Guestbook.query.filter_by(GuestbookID=book_id).first_or_404()
        content = jsonify({
            "guestbook": [{
                "id": book.GuestbookID,
                "name": book.Author,
                "message": book.Message,
                "isGuest": book.UserID == 1,
                "adminComment": book.AdminComment,
                "createdAt": book.Created,
                "updatedAt": book.Updated,
            }]
        })

        return make_response(content, 200)

    def post(self):
        """Add a new Guestbook post. If user is not logged in (userID = 1), then validate the
        username against existing users. If a registered user exists by the given name, then do not
        commit to DB and return a 400 Bad Request with a message that user should use a different
        name as the name is already used by a registered user."""
        data = json.loads(request.data.decode())

        # Check the username
        if (
            "userID" not in data
            or data["userID"] == 1
        ):
            exists = Users.query.filter_by(Name=data["name"]).first()
            if exists:
                error = {"success": False, "error": "Username already in use by a registered user"}
                return make_response(jsonify(error), 400)

        book = Guestbook(
            Author=data["name"],
            Message=data["message"],
            UserID=data["userID"],
            Created=get_datetime(),
        )
        db.session.add(book)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("GuestbookView:index"),
            book.GuestbookID
        )

        return make_response(jsonify(contents), 201)

    @admin_only
    def patch(self, book_id):
        """Admin-only. Partially modify the specified guestbook post."""
        book = Guestbook.query.filter_by(GuestbookID=book_id).first_or_404()
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(book, request.get_json())
            db.session.commit()
        except Exception as e:
            # If any other exceptions happened during the patching, we'll return 422
            print(e)
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)

    @admin_only
    def delete(self, book_id):
        """Admin-only. Delete the specified guestbook post."""
        book = Guestbook.query.filter_by(GuestbookID=book_id).first_or_404()
        db.session.delete(book)
        db.session.commit()
        return make_response("", 204)
