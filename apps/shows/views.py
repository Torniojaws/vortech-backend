import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from sqlalchemy import asc
from dictalchemy import make_class_dictable

from app import db, cache
from apps.shows.add_bps import add_bands, add_people, add_setlist
from apps.shows.models import Shows, ShowsOtherBands, ShowsPeopleMapping, ShowsSongsMapping
from apps.shows.patches import patch_item
from apps.utils.time import get_iso_format

make_class_dictable(Shows)


class ShowsView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all shows ordered by ShowID, ID=1 first"""
        shows = Shows.query.order_by(asc(Shows.ShowID)).all()
        content = jsonify({
            "shows": [{
                "date": get_iso_format(show.ShowDate),
                "countryCode": show.CountryCode,
                "country": show.Country,
                "city": show.City,
                "venue": show.Venue,
                "setlist": self.get_setlist(show.ShowID),
                "otherBands": self.get_other_bands(show.ShowID),
                "people": self.get_show_people(show.ShowID),
            } for show in shows]
        })

        return make_response(content, 200)

    @cache.cached(timeout=300)
    def get(self, show_id):
        """Return the details of the specified show."""
        show = Shows.query.filter_by(ShowID=show_id).first_or_404()
        content = jsonify({
            "shows": [{
                "date": get_iso_format(show.ShowDate),
                "countryCode": show.CountryCode,
                "country": show.Country,
                "city": show.City,
                "venue": show.Venue,
                "setlist": self.get_setlist(show.ShowID),
                "otherBands": self.get_other_bands(show.ShowID),
                "people": self.get_show_people(show.ShowID),
            }]
        })

        return make_response(content, 200)

    def post(self):
        """Add a new Show."""
        # TODO: Maybe allow adding multiple shows at once?
        data = json.loads(request.data.decode())
        show = Shows(
            ShowDate=data["showDate"],
            CountryCode=data["countryCode"],
            Country=data["country"],
            City=data["city"],
            Venue=data["venue"],
        )
        db.session.add(show)
        db.session.commit()

        # There is a change we also received extra details. Add them if so:
        if "otherBands" in data:
            add_bands(show.ShowID, data["otherBands"])

        if "people" in data:
            add_people(show.ShowID, data["people"])

        if "setlist" in data:
            add_setlist(show.ShowID, data["setlist"])

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("ShowsView:index"),
            show.ShowID
        )

        return make_response(jsonify(contents), 201)

    def put(self, show_id):
        """Overwrite all the data of the specified show."""
        data = json.loads(request.data.decode())
        show = Shows.query.filter_by(ShowID=show_id).first_or_404()

        # Update the Show
        show.ShowDate = data["showDate"]
        show.CountryCode = data["countryCode"]
        show.Country = data["country"]
        show.City = data["city"]
        show.Venue = data["venue"]

        # Remove any existing BPS for this show, and add the new ones
        self.clear_bps(show.ShowID)
        if "otherBands" in data:
            add_bands(show.ShowID, data["otherBands"])

        if "people" in data:
            add_people(show.ShowID, data["people"])

        if "setlist" in data:
            add_setlist(show.ShowID, data["setlist"])

        db.session.commit()

        return make_response("", 200)

    def patch(self, show_id):
        """Partially modify the specified show."""
        song = Shows.query.filter_by(ShowID=show_id).first_or_404()
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(song, request.get_json())
            db.session.commit()
        except Exception as e:
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)

    def delete(self, show_id):
        """Delete the specified show."""
        song = Shows.query.filter_by(ShowID=show_id).first_or_404()
        db.session.delete(song)
        db.session.commit()
        return make_response("", 204)

    def get_other_bands(self, show_id):
        """Return the list of other bands for a given show."""
        result = []
        for band in ShowsOtherBands.query.filter_by(ShowID=show_id).all():
            bd = {
                "name": band.BandName,
                "website": band.BandWebsite,
            }
            result.append(bd)
        return result

    def get_setlist(self, show_id):
        """Return the setlist for a given show in SetlistOrder."""
        songs = ShowsSongsMapping.query.filter_by(ShowID=show_id).order_by(
            asc(ShowsSongsMapping.SetlistOrder)).all()

        result = []
        for song in songs:
            sd = {
                "setlistOrder": song.SetlistOrder,
                "showID": song.ShowID,
                "songID": song.SongID,
                "duration": song.ShowSongDuration,
            }
            result.append(sd)
        return result

    def get_show_people(self, show_id):
        """Return the people and their instruments for a given show."""
        result = []
        for person in ShowsPeopleMapping.query.filter_by(ShowID=show_id).all():
            pd = {
                "showID": person.ShowID,
                "personID": person.PersonID,
                "instruments": person.Instruments,
            }
            result.append(pd)
        return result

    def clear_bps(self, show_id):
        """Remove all BPS (Bands, People, Setlist) entries for this show."""
        for band in ShowsOtherBands.query.filter_by(ShowID=show_id).all():
            db.session.delete(band)

        for person in ShowsPeopleMapping.query.filter_by(ShowID=show_id).all():
            db.session.delete(person)

        for setlist in ShowsSongsMapping.query.filter_by(ShowID=show_id).all():
            db.session.delete(setlist)

        db.session.commit()
