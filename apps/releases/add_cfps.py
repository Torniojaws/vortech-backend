"""Since the insertion of the CFPS (Categories, Formats, People, Songs) gets quite complex, the
POST /releases handling for them is in this separate file."""

from app import db
from apps.releases.models import (
    ReleasesCategoriesMapping, ReleaseCategories,
    ReleaseFormats, ReleasesFormatsMapping
)


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
    for rformat in formats:
        # Cast to string to avoid AttributeError: 'int' object has no attribute 'isdigit'
        if str(format).isdigit() is False:
            # Potentially a new format
            exists = ReleaseFormats.query.filter_by(ReleaseFormat=rformat).first()
            if exists:
                # Get the ID of the existing string
                format_id = exists.ReleaseFormatID
            else:
                # Insert a new format
                f = ReleaseFormats(
                    ReleaseFormat=rformat
                )
                db.session.add(f)
                db.session.commit()
                format_id = f.ReleaseFormatID
        else:
            # Verify that it does exist
            id_exists = ReleaseFormats.query.filter_by(ReleaseFormatID=rformat).first()
            if not id_exists:
                # Invalid ID was given, so we cannot proceed. It wouldn't make sense to insert a
                # number as the name of the format. No need to throw.
                continue
            else:
                format_id = rformat

        # Map format to the current release
        mapping = ReleasesFormatsMapping(
            ReleaseID=release_id,
            ReleaseFormatID=format_id,
        )
        db.session.add(mapping)
        db.session.commit()


def add_people(release_id, people):
    """Add people for the release. If the value is an integer, it references an existing person.
    If it is a string, it is potentially a new person. If no matches are found for the string, we
    create a new people entry and use its ID for this release."""


def add_songs(release_id, songs):
    """Add songs for the release. If the value is an integer, it references an existing song.
    If it is a string, it is potentially a new song. If no matches are found for the string, we
    create a new songs entry and use its ID for this release."""
