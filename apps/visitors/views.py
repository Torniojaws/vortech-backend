import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView
from geolite2 import geolite2

from app import db, cache
from apps.utils.time import get_date, get_datetime, get_monday, get_first_day
from apps.visitors.models import Visitors


class VisitorsView(FlaskView):
    @cache.cached(timeout=30)
    def index(self):
        """Return the amount of visits for today, this week, this month, and all time."""
        today = Visitors.query.filter(Visitors.VisitDate >= get_date()).count()
        week = Visitors.query.filter(Visitors.VisitDate >= get_monday()).count()
        month = Visitors.query.filter(Visitors.VisitDate >= get_first_day()).count()
        # The date 2017-11-01 is the first day of the month the new site went live.
        alltime = Visitors.query.filter(Visitors.VisitDate >= "2017-11-01").count()

        content = jsonify({
            "visits": {
                "today": today,
                "week": week,
                "month": month,
                "all": alltime,
            }
        })

        return make_response(content, 200)

    def post(self):
        """Add a new visit."""
        data = json.loads(request.data.decode())
        # This is just a simple thing to prevent accidental posts - we expect {"increment": 1}
        if "increment" not in data or data["increment"] != 1:
            error = {"success": False, "error": "Invalid data in visitor counter update"}
            return make_response(jsonify(error), 400)

        # Get visitor's Country and Continent based on the public IP address. Used for statistics.
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

        # If the IP is a local IP, geolite2 will return None and raise a TypeError
        try:
            reader = geolite2.reader()
            visitor_data = reader.get(ip_address)
            continent = visitor_data["continent"]["names"]["en"]
            country = visitor_data["country"]["names"]["en"]
        except TypeError:
            continent = "Unknown"
            country = "Unknown"

        visit = Visitors(
            VisitDate=get_datetime(),
            IPAddress=ip_address,
            Continent=continent,
            Country=country,
        )
        db.session.add(visit)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("VisitorsView:index"),
            visit.VisitID
        )

        return make_response(jsonify(contents), 201)
