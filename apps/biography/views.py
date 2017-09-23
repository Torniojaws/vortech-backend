import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import desc
from dictalchemy import make_class_dictable

from app import db
from apps.biography.models import Biography
from apps.biography.patches import patch_item
from apps.utils.time import get_datetime

make_class_dictable(Biography)


class BiographyView(FlaskView):
    def index(self):
        """Return the newest Biography entry."""
        newest = Biography.query.order_by(desc(Biography.BiographyID)).first_or_404()
        content = jsonify({
            "biography": [{
                "short": newest.Short,
                "full": newest.Full,
                "createdAt": newest.Created,
                "updatedAt": newest.Updated,
            }]
        })

        return make_response(content, 200)

    def post(self):
        """Add a new Biography entry."""
        data = json.loads(request.data.decode())
        bio = Biography(
            Short=data["short"],
            Full=data["full"],
            Created=get_datetime(),
        )
        db.session.add(bio)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("BiographyView:index"),
            bio.BiographyID
        )

        return make_response(jsonify(contents), 201)

    def put(self):
        """Overwrite the newest Biography with a new one."""
        data = json.loads(request.data.decode())
        bio = Biography.query.order_by(desc(Biography.BiographyID)).first_or_404()

        # Update the Biography
        bio.Short = data["short"]
        bio.Full = data["full"]
        bio.Updated = get_datetime()

        db.session.commit()

        return make_response("", 200)

    def patch(self):
        """Update the newest Biography entry partially."""
        bio = Biography.query.order_by(desc(Biography.BiographyID)).first_or_404()
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(bio, request.get_json())
            db.session.commit()
        except Exception as e:
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)
