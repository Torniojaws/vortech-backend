import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc

from app import db
from apps.downloads.models import DownloadsReleases
from apps.releases.models import Releases
from apps.utils.time import get_datetime, get_iso_format


class DownloadsView(FlaskView):
    """This is a bit special, since the base route will not really make sense for any situation.
    Instead, we'll have special routes for each type. Currently only Releases, though."""

    @route("/releases/", methods=["GET"])
    def all_release_downloads(self):
        """Return the download counts of all releases. Release 1 first. If a release does not have
        downloads, we return zeroes."""
        releases = Releases.query.order_by(asc(Releases.ReleaseID)).all()

        contents = jsonify({
            "downloads": [{
                "releaseID": release.ReleaseID,
                "count": self.get_download_count(release.ReleaseID),
                "since": self.get_first_download(release.ReleaseID),
            } for release in releases]
        })

        return make_response(contents, 200)

    @route("/releases/<int:release_id>", methods=["GET"])
    def release_downloads(self, release_id):
        """Return the download count for a specific release."""
        contents = jsonify({
            "downloads": [{
                "releaseID": release_id,
                "count": self.get_download_count(release_id),
                "since": self.get_first_download(release_id),
            }]
        })

        return make_response(contents, 200)

    @route("/releases/", methods=["POST"])
    def add_download(self):
        """Add a download to a release specified in the payload."""
        data = json.loads(request.data.decode())

        download = DownloadsReleases(
            ReleaseID=data["releaseID"],
            DownloadDate=get_datetime(),
        )
        db.session.add(download)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("DownloadsView:add_download"),
            data["releaseID"]
        )

        return make_response(contents, 201)

    def get_download_count(self, release_id):
        """Return the amount of downloads the release has."""
        return DownloadsReleases.query.filter_by(ReleaseID=release_id).count()

    def get_first_download(self, release_id):
        """Get the first date the specified release was downloaded on as ISO date."""
        date = DownloadsReleases.query.filter_by(ReleaseID=release_id).order_by(
            asc(DownloadsReleases.DownloadID)
        ).first().DownloadDate

        return get_iso_format(date)
