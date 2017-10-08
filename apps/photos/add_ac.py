from app import db
from apps.photos.models import (
    PhotoAlbums,
    PhotosAlbumsMapping,
    PhotoCategories,
    PhotosCategoriesMapping
)
from apps.utils.time import get_datetime


def add_album(photo_id, album):
    """Map the given album for the current photo. If the album value is a string,
    add it as a new album entry if it does not exist yet. A photo can only exist in one album."""
    # If for some reason we receive a List type, get the first value from it.
    if type(album) is list:
        album = album[0]

    photo_album_id = None
    if type(album) is int:
        # Possibly existing album
        exists = PhotoAlbums.query.filter_by(AlbumID=album).first()
        if exists:
            photo_album_id = exists.AlbumID
        else:
            # The ID is invalid, and we don't want to add a category with a number as name
            return
    else:
        # String album - add it as a new album, if there is no existing album with the same name
        exists = PhotoAlbums.query.filter_by(Title=album).first()
        if exists:
            photo_album_id = exists.AlbumID
        else:
            # Does not exist, let's add the new album
            new_album = PhotoAlbums(
                Title=album,
                Created=get_datetime()
            )
            db.session.add(new_album)
            db.session.commit()
            photo_album_id = new_album.AlbumID

    # Now that we have a valid PhotoAlbum ID, we can map it to the current Photo
    mapping = PhotosAlbumsMapping(
        PhotoID=photo_id,
        AlbumID=photo_album_id
    )
    db.session.add(mapping)
    db.session.commit()


def add_categories(photo_id, categories):
    """Insert the given categories for the current photo. If the category value is a string,
    add it as a new category entry if it does not exist yet."""
    # This allows non-list values to be processed, eg. "value": "somevalue"
    if type(categories) is not list:
        categories = [categories]

    for category in categories:
        photo_category_id = None
        if type(category) is int:
            # Possibly existing category
            exists = PhotoCategories.query.filter_by(PhotoCategoryID=category).first()
            if exists:
                photo_category_id = exists.PhotoCategoryID
            else:
                # The ID is invalid, and we don't want to add a category with a number as name
                print("")
                continue
        else:
            # String category - add it as a new category, if there is no existing category with
            # the same name
            exists = PhotoCategories.query.filter_by(Category=category).first()
            if exists:
                photo_category_id = exists.PhotoCategoryID
            else:
                # Does not exist, let's add the new category
                new_category = PhotoCategories(
                    Category=category
                )
                db.session.add(new_category)
                db.session.commit()
                photo_category_id = new_category.PhotoCategoryID

        # Now that we have a valid PhotoCategoryID, we can map it to the current VideoID
        mapping = PhotosCategoriesMapping(
            PhotoID=photo_id,
            PhotoCategoryID=photo_category_id
        )
        db.session.add(mapping)
        db.session.commit()
