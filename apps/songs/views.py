import json
import socket

from flask import jsonify, make_response, request, url_for
from flask_classful import FlaskView, route
from sqlalchemy import asc
from dictalchemy import make_class_dictable

from app import db, cache
from apps.songs.models import Songs, SongsLyrics
from apps.songs.patches import patch_item
from apps.utils.strings import linux_linebreaks

make_class_dictable(Songs)


class SongsView(FlaskView):
    @cache.cached(timeout=300)
    def index(self):
        """Return all songs ordered by SongID, ID=1 first"""
        songs = Songs.query.order_by(asc(Songs.SongID)).all()
        content = jsonify({
            "songs": [{
                "title": song.Title,
                "duration": song.Duration,
            } for song in songs]
        })

        return make_response(content, 200)

    @cache.cached(timeout=300)
    def get(self, song_id):
        """Return the details of the specified song."""
        song = Songs.query.filter_by(SongID=song_id).first_or_404()
        content = jsonify({
            "songs": [{
                "title": song.Title,
                "duration": song.Duration,
            }]
        })

        return make_response(content, 200)

    def post(self):
        """Add a new Song."""
        # TODO: Maybe allow adding multiple songs at once?
        data = json.loads(request.data.decode())
        song = Songs(
            Title=data["title"],
            Duration=data["duration"],
        )
        db.session.add(song)
        db.session.commit()

        # The RFC 7231 spec says a 201 Created should return an absolute full path
        server = socket.gethostname()
        contents = "Location: {}{}{}".format(
            server,
            url_for("SongsView:index"),
            song.SongID
        )

        return make_response(jsonify(contents), 201)

    def put(self, song_id):
        """Overwrite all the data of the specified song."""
        data = json.loads(request.data.decode())
        song = Songs.query.filter_by(SongID=song_id).first_or_404()

        # Update the Song
        song.Title = data["title"]
        song.Duration = data["duration"]

        db.session.commit()

        return make_response("", 200)

    def patch(self, song_id):
        """Partially modify the specified song."""
        song = Songs.query.filter_by(SongID=song_id).first_or_404()
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

    def delete(self, song_id):
        """Delete the specified song."""
        song = Songs.query.filter_by(SongID=song_id).first_or_404()
        db.session.delete(song)
        db.session.commit()
        return make_response("", 204)

    @route("/<int:song_id>/lyrics", methods=["GET"])
    @cache.cached(timeout=300)
    def song_lyrics(self, song_id):
        """Return the lyrics to a given Song"""
        song = Songs.query.filter_by(SongID=song_id).first_or_404()
        lyrics = SongsLyrics.query.filter_by(SongID=song_id).first_or_404()

        contents = jsonify({
            "songTitle": song.Title,
            "lyrics": linux_linebreaks(lyrics.Lyrics),
            "author": lyrics.Author
        })
        return make_response(contents, 200)
