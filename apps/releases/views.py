import json
import socket

from dictalchemy import make_class_dictable
from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc, desc

from app import db, cache
from apps.people.models import ReleasesPeopleMapping, People
from apps.releases.add_cfps import add_categories, add_formats, add_people, add_songs
from apps.releases.models import (
    Releases, ReleasesCategoriesMapping, ReleasesFormatsMapping, ReleaseFormats, ReleaseCategories,
    ReleasesReports
)
from apps.releases.patches import patch_item
from apps.songs.models import ReleasesSongsMapping, Songs
from apps.utils.auth import admin_only
from apps.utils.strings import linux_linebreaks
from apps.utils.time import get_datetime, get_iso_format

make_class_dictable(Releases)
make_class_dictable(ReleasesCategoriesMapping)
make_class_dictable(ReleasesFormatsMapping)
make_class_dictable(ReleasesPeopleMapping)
make_class_dictable(ReleasesSongsMapping)


class ReleasesView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all releases in reverse chronological order."""
        contents = jsonify({
            "releases": [{
                "id": release.ReleaseID,
                "releaseCode": release.ReleaseCode,
                "title": release.Title,
                "releaseDate": get_iso_format(release.Date),
                "artist": release.Artist,
                "credits": release.Credits,
                "formats": self.get_formats(release.ReleaseID),
                "categories": self.get_categories(release.ReleaseID),
                "songs": self.get_songs(release.ReleaseID),
                "people": self.get_people(release.ReleaseID),
                "created": get_iso_format(release.Created),
                "updated": get_iso_format(release.Updated),
            } for release in Releases.query.filter(
                Releases.Date <= get_datetime()
            ).order_by(desc(Releases.ReleaseID)).all()]
        })
        return make_response(contents, 200)

    @cache.cached(timeout=300)
    def get(self, release_id):
        """Return a specific release"""
        release = Releases.query.filter_by(ReleaseID=release_id).first_or_404()
        contents = jsonify({
            "releases": [{
                "id": release.ReleaseID,
                "releaseCode": release.ReleaseCode,
                "title": release.Title,
                "releaseDate": get_iso_format(release.Date),
                "artist": release.Artist,
                "credits": release.Credits,
                "categories": self.get_categories(release.ReleaseID),
                "formats": self.get_formats(release.ReleaseID),
                "people": self.get_people(release.ReleaseID),
                "songs": self.get_songs(release.ReleaseID),
                "created": get_iso_format(release.Created),
                "updated": get_iso_format(release.Updated),
            }]
        })
        return make_response(contents, 200)

    @admin_only
    def post(self):
        """Add a new release and its related CFPS details. This gets quite complex due to
        four different inserts and checks in some of them, so the actual implementation will be
        in its own file."""
        data = json.loads(request.data.decode())
        release = Releases(
            ReleaseCode=data["releaseCode"],
            Title=data["title"],
            Date=data["releaseDate"],
            Artist=data["artist"],
            Credits=data["credits"],
            Created=get_datetime(),
        )
        db.session.add(release)
        db.session.commit()

        # Now that the release exists, we can insert the CFPS
        add_categories(release.ReleaseID, data["categories"])
        add_formats(release.ReleaseID, data["formats"])
        add_people(release.ReleaseID, data["people"])
        add_songs(release.ReleaseID, data["songs"])

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = jsonify("Location: {}{}{}".format(
            server,
            url_for("ReleasesView:index"),
            release.ReleaseID
        ))

        return make_response(contents, 201)

    @admin_only
    def put(self, release_id):
        """Replace the data of a specific release"""
        data = json.loads(request.data.decode())
        release = Releases.query.get_or_404(release_id)

        # Update the release
        release.ReleaseCode = data["releaseCode"]
        release.Title = data["title"]
        release.Date = data["releaseDate"]
        release.Artist = data["artist"]
        release.Credits = data["credits"]
        release.Updated = get_datetime()

        # Update Categories. Since they are one per row, we'll just delete and add.
        db.session.query(ReleasesCategoriesMapping).filter_by(ReleaseID=release_id).delete()
        db.session.commit()
        add_categories(release_id, data["categories"])

        # Update Formats. Since they are one per row, we'll just delete and add.
        db.session.query(ReleasesFormatsMapping).filter_by(ReleaseID=release_id).delete()
        db.session.commit()
        add_formats(release_id, data["formats"])

        # Update People. Since they are one per row, we'll just delete and add.
        db.session.query(ReleasesPeopleMapping).filter_by(ReleaseID=release_id).delete()
        db.session.commit()
        add_people(release_id, data["people"])

        # Update Songs. Since they are one per row, we'll just delete and add.
        db.session.query(ReleasesSongsMapping).filter_by(ReleaseID=release_id).delete()
        db.session.commit()
        add_songs(release_id, data["songs"])

        return make_response("", 200)

    @admin_only
    def patch(self, release_id):
        """Partially update a specific release"""
        release = Releases.query.get_or_404(release_id)
        result = []
        status_code = 204
        try:
            # This only returns a value (boolean) for "op": "test"
            result = patch_item(release, request.get_json())
            db.session.commit()
        except Exception as e:
            print(e)
            # If any other exceptions happened during the patching, we'll return 422
            result = {"success": False, "error": "Could not apply patch"}
            status_code = 422

        return make_response(jsonify(result), status_code)

    @admin_only
    def delete(self, release_id):
        """Delete a Release"""
        release = Releases.query.filter_by(ReleaseID=release_id).first()
        db.session.delete(release)
        db.session.commit()

        return make_response("", 204)

    def get_categories(self, release_id):
        """Return all the categories that the release is assigned to"""
        release_categories = ReleasesCategoriesMapping.query.filter_by(
            ReleaseID=release_id
        ).order_by(
            asc(ReleasesCategoriesMapping.ReleaseCategoryID)
        ).all()

        # Get the values
        categories = []
        for release_cat in release_categories:
            category = ReleaseCategories.query.filter_by(
                ReleaseCategoryID=release_cat.ReleaseCategoryID
            ).first()
            categories.append(category.ReleaseCategory)

        return categories

    def get_formats(self, release_id):
        """Return all the formats assigned to the release"""
        release_formats = ReleasesFormatsMapping.query.filter_by(
            ReleaseID=release_id
        ).order_by(
            asc(ReleasesFormatsMapping.ReleaseFormatID)
        ).all()

        # Get the values
        formats = []
        for release_format in release_formats:
            _format = ReleaseFormats.query.filter_by(
                ReleaseFormatID=release_format.ReleaseFormatID
            ).first()
            formats.append(
                _format.Title
            )

        return formats

    def get_people(self, release_id):
        """Return all the people that were part of the release"""
        release_people = ReleasesPeopleMapping.query.filter_by(
            ReleaseID=release_id
        ).order_by(
            asc(ReleasesPeopleMapping.PersonID)
        ).all()

        # Retrieve the data for each personID
        people = []
        for release_person in release_people:
            person = People.query.filter_by(PersonID=release_person.PersonID).first()
            people.append(
                dict(
                    name=person.Name,
                    instruments=release_person.Instruments,
                )
            )

        return people

    def get_songs(self, release_id):
        """Return all the songs that were on the release"""
        release_songs = ReleasesSongsMapping.query.filter_by(
            ReleaseID=release_id
        ).order_by(
            asc(ReleasesSongsMapping.ReleasesSongsMappingID)
        ).all()

        # Then retrieve the data of the songs
        songs = []
        for release_song in release_songs:
            song = Songs.query.filter_by(SongID=release_song.SongID).first()
            songs.append(
                dict(
                    title=song.Title,
                    duration=song.Duration,
                    id=song.SongID,
                )
            )

        return songs

    @route("/<int:release_id>/studio-report", methods=["GET"])
    @cache.cached(timeout=300)
    def release_studio_report(self, release_id):
        """Return the studio report(s) to a given Release, in order of their write date.
        There might be multiple reports."""
        release = Releases.query.filter_by(ReleaseID=release_id).first_or_404()

        contents = jsonify({
            "reports": [{
                "reportID": report.ReleasesReportsID,
                "releaseID": report.ReleaseID,
                "report": linux_linebreaks(report.Report),
                "author": report.Author,
                "date": get_iso_format(report.ReportDate),
                "created_at": get_iso_format(report.Created),
                "updated_at": get_iso_format(report.Updated)
            } for report in ReleasesReports.query.filter_by(
                ReleaseID=release.ReleaseID
            ).order_by(asc(ReleasesReports.ReportDate)).all()]
        })
        return make_response(contents, 200)
