"""This contains the extra functions used to add BPS (Bands, People, Songs)"""

from app import db
from apps.shows.models import ShowsOtherBands, ShowsPeopleMapping, ShowsSongsMapping


def add_bands(show_id, bands):
    """Insert the bands to the given Show."""
    for band in bands:
        show_band = ShowsOtherBands(
            ShowID=show_id,
            BandName=band["bandName"],
            BandWebsite=band["bandWebsite"],
        )
        db.session.add(show_band)
    db.session.commit()


def add_people(show_id, people):
    """Insert the people to the given show."""
    # TODO: If person is a string, add a new person
    for person in people:
        show_person = ShowsPeopleMapping(
            ShowID=show_id,
            PersonID=person["personID"],
            Instruments=person["instruments"],
        )
        db.session.add(show_person)
    db.session.commit()


def add_setlist(show_id, setlist):
    """Insert the setlist to the given show."""
    for song in setlist:
        show_song = ShowsSongsMapping(
            ShowID=show_id,
            SongID=song["songID"],
            SetlistOrder=song["setlistOrder"],
            ShowSongDuration=song["duration"],
        )
        db.session.add(show_song)
    db.session.commit()
