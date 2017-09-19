"""Since the insertion of the CFPS (Categories, Formats, People, Songs) gets quite complex, the
POST /releases handling for them is in this separate file."""

from app import db
from apps.releases.models import (
    ReleasesCategoriesMapping, ReleaseCategories,
    ReleaseFormats, ReleasesFormatsMapping
)
from apps.people.models import People, ReleasesPeopleMapping
from apps.songs.models import Songs, ReleasesSongsMapping

# TODO: add_categories() and add_formats() are pretty much identical. The only differences are the
# DB Models in use and the column names we compare to. Could they be simplified to one add()
# method?
# NB: add_people() and add_songs() are also similar, but they have unique columns that we add to,
# so they cannot be merged into one method.


def add_categories(release_id, categories):
    """Add the categories for the release. If the value is an integer, it references an existing
    release category. If it is a string, it is potentially a new category. If no matches are found
    for the string, we create a new release category entry and then use its ID for this release."""
    for category in categories:
        # Cast to string to avoid AttributeError: 'int' object has no attribute 'isdigit'
        if str(category).isdigit() is False:
            # Potentially a new category
            exists = ReleaseCategories.query.filter_by(ReleaseCategory=category).first()
            if exists:
                # Get the ID of the existing string
                category_id = exists.ReleaseCategoryID
            else:
                # Insert a new category
                cat = ReleaseCategories(
                    ReleaseCategory=category
                )
                db.session.add(cat)
                db.session.commit()
                category_id = cat.ReleaseCategoryID
        else:
            # Verify that it does exist
            id_exists = ReleaseCategories.query.filter_by(ReleaseCategoryID=category).first()
            if not id_exists:
                # Invalid ID was given, so we cannot proceed. It wouldn't make sense to insert a
                # number as the name of the category. No need to throw.
                continue
            else:
                category_id = category

        # Map category to the current release
        mapping = ReleasesCategoriesMapping(
            ReleaseID=release_id,
            ReleaseCategoryID=category_id,
        )
        db.session.add(mapping)
        db.session.commit()


def add_formats(release_id, formats):
    """Add formats for the release. If the value is an integer, it references an existing release
    format entry. If it is a string, it is potentially a new format. If no matches are found for
    the string, we create a new release format entry and use its ID for this release."""
    for release_format in formats:
        format_id = None
        if type(release_format) is int:
            # Potentially an existing ID
            id_exists = ReleaseFormats.query.filter_by(ReleaseFormatID=release_format).first()
            if id_exists:
                format_id = id_exists.ReleaseFormatID
            else:
                # The ID does not exist, so we ignore this format and continue with the next
                # NB: Pytest has a bug regarding continue, which results in it being marked as
                # not covered - see:
                # https://bitbucket.org/ned/coveragepy/issues/198/continue-marked-as-not-covered
                continue  # pragma: no cover
        else:
            # Check does a format exist by that string?
            string_exists = ReleaseFormats.query.filter_by(Title=release_format).first()
            if string_exists:
                # Yep! Use its ID for mapping.
                format_id = string_exists.ReleaseFormatID
            else:
                # Nope. Let's insert it and then use the shiny new ID
                rf = ReleaseFormats(
                    Title=release_format
                )
                db.session.add(rf)
                db.session.commit()
                format_id = rf.ReleaseFormatID

        # Do the mapping
        mapping = ReleasesFormatsMapping(
            ReleaseFormatID=format_id,
            ReleaseID=release_id,
        )
        db.session.add(mapping)
        db.session.commit()


def add_people(release_id, people):
    """Add people for the release. If the value is an integer, it references an existing person.
    If it is a string, it is potentially a new person. If no matches are found for the string, we
    create a new people entry and use its ID for this release.

    Each person also comes with instruments! That will be mapped on a per-release basis, so that
    the same PersonID can play guitar on one album and drums on another.

    For example: [{1: "Guitar"}, {"Mike": "Drums"}]
    1 = The ID of an existing person.
    "Mike" = a new person, to be added to the table People
    """
    for person in people:
        # Get the values
        for k, v in person.items():
            identifier = k
            instruments = v

        person_id = None
        if type(identifier) is int:
            id_exists = People.query.filter_by(PersonID=identifier).first()
            if id_exists:
                person_id = id_exists.PersonID
            else:
                # The person ID is invalid, so we will not map it at all.
                # NB: Pytest has a bug regarding continue, which results in it being marked as
                # not covered - see:
                # https://bitbucket.org/ned/coveragepy/issues/198/continue-marked-as-not-covered
                continue  # pragma: no cover
        else:
            name_exists = People.query.filter_by(Name=identifier).first()
            if name_exists:
                person_id = name_exists.PersonID
            else:
                new_person = People(
                    Name=identifier
                )
                db.session.add(new_person)
                db.session.commit()
                person_id = new_person.PersonID

        # Map to a release
        mapping = ReleasesPeopleMapping(
            ReleaseID=release_id,
            PersonID=person_id,
            Instruments=instruments,
        )
        db.session.add(mapping)
        db.session.commit()


def add_songs(release_id, songs):
    """Add songs for the release. If the value is an integer, it references an existing song.
    If it is a string, it is potentially a new song. If no matches are found for the string, we
    create a new songs entry and use its ID for this release.

    Each song also has a duration in seconds. This is stored to Songs.

    eg. [{"Song Title": 123}, {1: 321}]
    "Song Title" = new song to be added to Songs
    1 = Refers to an existing song by ID=1

    NB: The Duration is ignored for existing songs.
    """
    for song in songs:
        # Get the data
        for k, v in song.items():
            identifier = k
            duration = v
        song_id = None
        if type(identifier) is int:
            id_exists = Songs.query.filter_by(SongID=identifier).first()
            if id_exists:
                song_id = id_exists.SongID
            else:
                # NB: Pytest has a bug regarding continue, which results in it being marked as
                # not covered - see:
                # https://bitbucket.org/ned/coveragepy/issues/198/continue-marked-as-not-covered
                continue  # pragma: no cover
        else:
            song_exists = Songs.query.filter_by(Title=identifier).first()
            if song_exists:
                song_id = song_exists.SongID
            else:
                new_song = Songs(
                    Title=identifier,
                    Duration=duration,
                )
                db.session.add(new_song)
                db.session.commit()
                song_id = new_song.SongID

        # Map to a release
        mapping = ReleasesSongsMapping(
            ReleaseID=release_id,
            SongID=song_id,
            ReleaseSongDuration=duration,
        )
        db.session.add(mapping)
        db.session.commit()
