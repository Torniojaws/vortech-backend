import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import desc
from dictalchemy import make_class_dictable

from app import db
from apps.contacts.models import Contacts
from apps.contacts.patches import patch_item
from apps.utils.time import get_datetime

make_class_dictable(Contacts)


class ContactsView(FlaskView):
    def index(self):
        """Return the newest Contacts entry."""
        contact = Contacts.query.order_by(desc(Contacts.Created)).first_or_404()
        content = jsonify({
            "contacts": [{
                "id": contact.ContactsID,
                "email": contact.Email,
                "techRider": contact.TechRider,
                "inputList": contact.InputList,
                "backline": contact.Backline,
                "createdAt": contact.Created,
                "updatedAt": contact.Updated,
            }]
        })

        return make_response(content, 200)

    def post(self):
        """Add a new Contacts entry."""
        data = json.loads(request.data.decode())
        contact = Contacts(
            Email=data["email"],
            TechRider=data["techRider"],
            InputList=data["inputList"],
            Backline=data["backline"],
            Created=get_datetime(),
        )
        db.session.add(contact)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("ContactsView:index"),
            contact.ContactsID
        )

        return make_response(jsonify(contents), 201)

    def patch(self):
        """Partially modify the newest contact."""
        contact = Contacts.query.order_by(desc(Contacts.Created)).first_or_404()
        result = []
        status_code = 204
        try:
            result = patch_item(contact, request.get_json())
            db.session.commit()
        except Exception as e:
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)
