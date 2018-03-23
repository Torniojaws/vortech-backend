import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import asc

from app import db, cache
from apps.people.models import People, ReleasesPeopleMapping
from apps.shows.models import ShowsPeopleMapping


class PeopleView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all people ordered by PersonID, ID=1 first"""
        people = People.query.order_by(asc(People.PersonID)).all()
        content = jsonify({
            "people": [{
                "name": person.Name,
                "releases": self.get_releases(person.PersonID),
                "shows": self.get_shows(person.PersonID),
            } for person in people]
        })

        return make_response(content, 200)

    @cache.cached(timeout=300)
    def get(self, person_id):
        """Return the details of the specified person."""
        person = People.query.filter_by(PersonID=person_id).first_or_404()
        content = jsonify({
            "people": [{
                "name": person.Name,
                "releases": self.get_releases(person.PersonID),
                "shows": self.get_shows(person.PersonID),
            }]
        })

        return make_response(content, 200)

    def post(self):
        """Add a new Person."""
        data = json.loads(request.data.decode())
        person = People(
            Name=data["name"],
        )
        db.session.add(person)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("PeopleView:index"),
            person.PersonID
        )

        return make_response(jsonify(contents), 201)

    def put(self, person_id):
        """Rename the specified person."""
        data = json.loads(request.data.decode())
        person = People.query.filter_by(PersonID=person_id).first_or_404()

        person.Name = data["name"]

        db.session.commit()

        return make_response("", 200)

    def delete(self, person_id):
        """Delete the specified person."""
        person = People.query.filter_by(PersonID=person_id).first_or_404()
        db.session.delete(person)
        db.session.commit()
        return make_response("", 204)

    def get_releases(self, person_id):
        """Get the ReleaseIDs and instruments the Person appeared on."""
        result = []
        for release in ReleasesPeopleMapping.query.filter_by(PersonID=person_id).all():
            r = {
                "releaseID": release.ReleaseID,
                "instruments": release.Instruments
            }
            result.append(r)
        return result

    def get_shows(self, person_id):
        """Get the ShowIDs and instruments the Person played on."""
        result = []
        for show in ShowsPeopleMapping.query.filter_by(PersonID=person_id).all():
            s = {
                "showID": show.ShowID,
                "instruments": show.Instruments
            }
            result.append(s)
        return result
