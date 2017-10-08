import json
import unittest

from app import app, db
from apps.photos.models import (
    Photos,
    PhotoAlbums,
    PhotosAlbumsMapping,
    PhotoCategories,
    PhotosCategoriesMapping
)


class TestPhotosViews(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        # Create a few Photo Albums and Categories
        album1 = PhotoAlbums(
            Title="UnitTest Photo Album 1",
            Created="2017-05-05 05:05:05"
        )
        album2 = PhotoAlbums(
            Title="UnitTest Photo Album 2",
            Created="2017-06-06 06:06:06"
        )
        db.session.add(album1)
        db.session.add(album2)
        db.session.commit()
        self.valid_albums = [album1.AlbumID, album2.AlbumID]

        cat1 = PhotoCategories(
            Category="UnitTest Category 1"
        )
        cat2 = PhotoCategories(
            Category="UnitTest Category 2"
        )
        cat3 = PhotoCategories(
            Category="UnitTest Category 3"
        )
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.add(cat3)
        db.session.commit()
        self.valid_cats = [cat1.PhotoCategoryID, cat2.PhotoCategoryID, cat3.PhotoCategoryID]

        # And then add some photos
        photo1 = Photos(
            Image="unittest1.jpg",
            Caption="UnitTest Caption 1",
            TakenBy="UnitTest Taken 1",
            Country="UnitTest Country 1",
            CountryCode="UT",
            City="UnitTest City 1",
            Created="2017-09-09 09:09:09"
        )
        photo2 = Photos(
            Image="unittest2.jpg",
            Caption="UnitTest Caption 2",
            TakenBy="UnitTest Taken 2",
            Country="UnitTest Country 2",
            CountryCode="UT",
            City="UnitTest City 2",
            Created="2017-09-10 09:09:09"
        )
        photo3 = Photos(
            Image="unittest3.jpg",
            Caption="UnitTest Caption 3",
            TakenBy="UnitTest Taken 3",
            Country="UnitTest Country 3",
            CountryCode="UT",
            City="UnitTest City 3",
            Created="2017-09-11 09:09:09"
        )
        db.session.add(photo1)
        db.session.add(photo2)
        db.session.add(photo3)
        db.session.commit()
        self.valid_photos = [photo1.PhotoID, photo2.PhotoID, photo3.PhotoID]

        # And finally, map the photos to albums and categories
        photo1_album = PhotosAlbumsMapping(
            PhotoID=photo1.PhotoID,
            AlbumID=album1.AlbumID
        )
        photo2_album = PhotosAlbumsMapping(
            PhotoID=photo2.PhotoID,
            AlbumID=album1.AlbumID
        )
        photo3_album = PhotosAlbumsMapping(
            PhotoID=photo3.PhotoID,
            AlbumID=album2.AlbumID
        )
        db.session.add(photo1_album)
        db.session.add(photo2_album)
        db.session.add(photo3_album)
        db.session.commit()

        photo1_cat1 = PhotosCategoriesMapping(
            PhotoID=photo1.PhotoID,
            PhotoCategoryID=cat1.PhotoCategoryID
        )
        photo1_cat2 = PhotosCategoriesMapping(
            PhotoID=photo1.PhotoID,
            PhotoCategoryID=cat2.PhotoCategoryID
        )
        photo2_cat1 = PhotosCategoriesMapping(
            PhotoID=photo2.PhotoID,
            PhotoCategoryID=cat1.PhotoCategoryID
        )
        photo3_cat3 = PhotosCategoriesMapping(
            PhotoID=photo3.PhotoID,
            PhotoCategoryID=cat3.PhotoCategoryID
        )
        db.session.add(photo1_cat1)
        db.session.add(photo1_cat2)
        db.session.add(photo2_cat1)
        db.session.add(photo3_cat3)
        db.session.commit()

    def tearDown(self):
        for album in PhotoAlbums.query.filter(PhotoAlbums.Title.like("UnitTest%")).all():
            db.session.delete(album)
        db.session.commit()

        for cat in PhotoCategories.query.filter(
            PhotoCategories.Category.like("UnitTest%")
        ).all():
            db.session.delete(cat)
        db.session.commit()

        for photo in Photos.query.filter(Photos.Image.like("unittest%")).all():
            db.session.delete(photo)
        db.session.commit()

    def test_getting_all_photos(self):
        """Should return all photos in asc PhotoID order."""
        response = self.app.get("/api/1.0/photos/")
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(3, len(data["photos"]))
        self.assertEquals("unittest1.jpg", data["photos"][0]["image"])
        self.assertEquals("unittest2.jpg", data["photos"][1]["image"])
        self.assertEquals("unittest3.jpg", data["photos"][2]["image"])

        self.assertEquals(self.valid_photos[0], data["photos"][0]["id"])
        self.assertEquals("UnitTest Caption 1", data["photos"][0]["caption"])
        self.assertEquals("UnitTest Taken 1", data["photos"][0]["takenBy"])
        self.assertEquals("UnitTest Country 1", data["photos"][0]["country"])
        self.assertEquals("UT", data["photos"][0]["countryCode"])
        self.assertEquals("UnitTest City 1", data["photos"][0]["city"])
        self.assertNotEquals("", data["photos"][0]["createdAt"])
        self.assertEquals(None, data["photos"][0]["updatedAt"])

        self.assertEquals(self.valid_albums[0], data["photos"][0]["albumID"])
        self.assertEquals(self.valid_albums[0], data["photos"][1]["albumID"])
        self.assertEquals(self.valid_albums[1], data["photos"][2]["albumID"])

        self.assertEquals(
            [self.valid_cats[0], self.valid_cats[1]],
            data["photos"][0]["categories"]
        )
        self.assertEquals([self.valid_cats[0]], data["photos"][1]["categories"])
        self.assertEquals([self.valid_cats[2]], data["photos"][2]["categories"])

    def test_getting_one_photo(self):
        """Should return the data of a given photo."""
        response = self.app.get("/api/1.0/photos/{}".format(self.valid_photos[1]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(data["photos"]))
        self.assertEquals("unittest2.jpg", data["photos"][0]["image"])

        self.assertEquals(self.valid_photos[1], data["photos"][0]["id"])
        self.assertEquals("UnitTest Caption 2", data["photos"][0]["caption"])
        self.assertEquals("UnitTest Taken 2", data["photos"][0]["takenBy"])
        self.assertEquals("UnitTest Country 2", data["photos"][0]["country"])
        self.assertEquals("UT", data["photos"][0]["countryCode"])
        self.assertEquals("UnitTest City 2", data["photos"][0]["city"])
        self.assertNotEquals("", data["photos"][0]["createdAt"])
        self.assertEquals(None, data["photos"][0]["updatedAt"])

        self.assertEquals(self.valid_albums[0], data["photos"][0]["albumID"])

        self.assertEquals([self.valid_cats[0]], data["photos"][0]["categories"])

    def test_getting_photos_in_album(self):
        """Should return all photos in a given album."""
        response = self.app.get("/api/1.0/photos/albums/{}".format(self.valid_albums[0]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len(data["photos"]))
        self.assertEquals("unittest1.jpg", data["photos"][0]["image"])
        self.assertEquals("unittest2.jpg", data["photos"][1]["image"])
        self.assertEquals(self.valid_albums[0], data["photos"][0]["albumID"])
        self.assertEquals(self.valid_albums[0], data["photos"][1]["albumID"])

    def test_getting_photos_in_category(self):
        """Should return all photos in a given photo category."""
        response = self.app.get("/api/1.0/photos/categories/{}".format(self.valid_cats[0]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(2, len(data["photos"]))
        self.assertEquals("unittest1.jpg", data["photos"][0]["image"])
        self.assertEquals("unittest2.jpg", data["photos"][1]["image"])
        # The same photo can be in multiple categories, so the exact entry must be checked
        self.assertEquals(self.valid_cats[0], data["photos"][0]["categories"][0])
        self.assertEquals(self.valid_cats[0], data["photos"][1]["categories"][0])

    def test_adding_photo(self):
        """Should add the photo and its related album and categories mapping."""
        response = self.app.post(
            "/api/1.0/photos/",
            data=json.dumps(
                dict(
                    image="unittest-post.jpg",
                    caption="UnitTest Post Caption",
                    takenBy="UnitTest Post Taken",
                    country="UnitTest Post Country",
                    countryCode="UT",
                    city="UnitTest Post City",
                    album=self.valid_albums[1],
                    categories=[self.valid_cats[0], self.valid_cats[1]]
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        photo = Photos.query.filter_by(Image="unittest-post.jpg").first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=photo.PhotoID).first()
        cats = PhotosCategoriesMapping.query.filter_by(PhotoID=photo.PhotoID).all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)

        self.assertEquals("unittest-post.jpg", photo.Image)
        self.assertEquals("UnitTest Post Caption", photo.Caption)
        self.assertEquals("UnitTest Post Taken", photo.TakenBy)
        self.assertEquals("UnitTest Post Country", photo.Country)
        self.assertEquals("UT", photo.CountryCode)
        self.assertEquals("UnitTest Post City", photo.City)

        self.assertEquals(self.valid_albums[1], album.AlbumID)
        self.assertEquals(
            [self.valid_cats[0], self.valid_cats[1]],
            [c.PhotoCategoryID for c in cats]
        )

    def test_patching_photo_using_add(self):
        """In practice, replace the existing value whether it's NULL or populated. In the case of
        categories, however, this should append to the existing values."""
        response = self.app.patch(
            "/api/1.0/photos/{}".format(self.valid_photos[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "add",
                        "path": "/caption",
                        "value": "UnitTest Patched Caption"
                    }),
                    dict({
                        "op": "add",
                        "path": "/album",
                        "value": self.valid_albums[1]
                    }),
                    dict({
                        "op": "add",
                        "path": "/categories",
                        "value": [self.valid_cats[2]]
                    }),
                ]
            ),
            content_type="application/json"
        )

        photo = Photos.query.filter_by(PhotoID=self.valid_photos[0]).first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=self.valid_photos[0]).first()
        cats = PhotosCategoriesMapping.query.filter_by(PhotoID=self.valid_photos[0]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        self.assertEquals("UnitTest Patched Caption", photo.Caption)
        self.assertEquals(self.valid_albums[1], album.AlbumID)
        self.assertEquals(3, len(cats))
        self.assertEquals(self.valid_cats[2], cats[2].PhotoCategoryID)

    def test_patching_photo_using_copy(self):
        """For the Photo data, anything goes. But for album and categories, there is really no
        sensible action, so they just skip the copy."""
        response = self.app.patch(
            "/api/1.0/photos/{}".format(self.valid_photos[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/caption",
                        "path": "/image"
                    }),
                    dict({
                        "op": "copy",
                        "from": "/album",
                        "path": "/takenBy"
                    }),
                    dict({
                        "op": "copy",
                        "from": "/categories",
                        "path": "/country"
                    }),
                ]
            ),
            content_type="application/json"
        )

        photo = Photos.query.filter_by(PhotoID=self.valid_photos[0]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        self.assertEquals("UnitTest Caption 1", photo.Image)
        # These are nonsense, but allows to test the "copy" operation validly. Since the method
        # skips the operation, the target value should remain identical.
        self.assertEquals("UnitTest Taken 1", photo.TakenBy)
        self.assertEquals("UnitTest Country 1", photo.Country)

    def test_patching_photo_using_move(self):
        """For the Photo data, anything goes. But for album and categories, there is really no
        sensible action, so they just skip the move."""
        response = self.app.patch(
            "/api/1.0/photos/{}".format(self.valid_photos[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "move",
                        "from": "/caption",
                        "path": "/takenBy"
                    }),
                    dict({
                        "op": "move",
                        "from": "/album",
                        "path": "/takenBy"
                    }),
                    dict({
                        "op": "move",
                        "from": "/categories",
                        "path": "/country"
                    }),
                ]
            ),
            content_type="application/json"
        )

        photo = Photos.query.filter_by(PhotoID=self.valid_photos[0]).first()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        # Due to JsonPatch and sqlalchemy differences in behaviour, the move keeps the original
        self.assertEquals("UnitTest Caption 1", photo.Caption)
        self.assertEquals("UnitTest Caption 1", photo.TakenBy)
        # These are nonsense, but allows to test the "copy" operation validly. Since the method
        # skips the operation, the target value should remain identical.
        # NB: This value is Caption 1, because we moved the caption to TakenBy above
        self.assertEquals("UnitTest Caption 1", photo.TakenBy)
        self.assertEquals("UnitTest Country 1", photo.Country)

    def test_patching_photo_using_remove(self):
        """Remove the given resource. Due to the usual JsonPatch+sqlalchemy, it won't work for
        Photos, but it should work for the mappings."""
        response = self.app.patch(
            "/api/1.0/photos/{}".format(self.valid_photos[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "remove",
                        "path": "/takenBy"
                    }),
                    dict({
                        "op": "remove",
                        "path": "/categories"
                    }),
                    dict({
                        "op": "remove",
                        "path": "/album"
                    }),
                ]
            ),
            content_type="application/json"
        )

        photo = Photos.query.filter_by(PhotoID=self.valid_photos[0]).first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=self.valid_photos[0]).first()
        cats = PhotosCategoriesMapping.query.filter_by(PhotoID=self.valid_photos[0]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        # Due to JsonPatch and sqlalchemy differences in behaviour, the move keeps the original
        self.assertEquals("UnitTest Taken 1", photo.TakenBy)
        self.assertEquals(None, album)
        self.assertEquals([], cats)

    def test_patching_photo_using_replace(self):
        """Replace the existing value."""
        response = self.app.patch(
            "/api/1.0/photos/{}".format(self.valid_photos[0]),
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/caption",
                        "value": "UnitTest Patched Caption"
                    }),
                    dict({
                        "op": "replace",
                        "path": "/album",
                        "value": [self.valid_albums[1]]  # We test using list here as extra test
                    }),
                    dict({
                        "op": "replace",
                        "path": "/categories",
                        "value": [self.valid_cats[2]]
                    }),
                ]
            ),
            content_type="application/json"
        )

        photo = Photos.query.filter_by(PhotoID=self.valid_photos[0]).first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=self.valid_photos[0]).first()
        cats = PhotosCategoriesMapping.query.filter_by(PhotoID=self.valid_photos[0]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        self.assertEquals("UnitTest Patched Caption", photo.Caption)
        self.assertEquals(self.valid_albums[1], album.AlbumID)
        self.assertEquals(1, len(cats))
        self.assertEquals(self.valid_cats[2], cats[0].PhotoCategoryID)

    def test_deleting_photo(self):
        """Should delete the photo and its mappings."""
        response = self.app.delete("/api/1.0/photos/{}".format(self.valid_photos[1]))

        photo = Photos.query.filter_by(PhotoID=self.valid_photos[1]).first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=self.valid_photos[1]).first()
        cats = PhotosCategoriesMapping.query.filter_by(PhotoID=self.valid_photos[1]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        self.assertEquals(None, photo)
        self.assertEquals(None, album)
        self.assertEquals([], cats)

    def test_failing_patch(self):
        """Should return a 422 Unprocessable Entity."""
        response = self.app.patch(
            "/api/1.0/photos/{}".format(self.valid_photos[0]),
            data=json.dumps(
                dict({
                    "op": "copy",
                    "from": "/DoesNotExist",
                    "path": "/something"
                })
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        self.assertEquals(422, response.status_code)
        self.assertFalse(data["success"])

    def test_adding_album_and_category_with_invalid_id(self):
        """When the ID is a non-existing integer, it should be skipped."""
        response = self.app.post(
            "/api/1.0/photos/",
            data=json.dumps(
                dict(
                    image="unittest-post.jpg",
                    caption="UnitTest Post Caption",
                    takenBy="UnitTest Post Taken",
                    country="UnitTest Post Country",
                    countryCode="UT",
                    city="UnitTest Post City",
                    album=0,
                    categories=0
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        photo = Photos.query.filter_by(Image="unittest-post.jpg").first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=photo.PhotoID).first()
        cats = PhotosCategoriesMapping.query.filter_by(PhotoID=photo.PhotoID).first()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertEquals(None, album)
        self.assertEquals(None, cats)

    def test_adding_album_with_existing_string(self):
        """When the Album ID is an existing string, we should not add a new entry."""
        response = self.app.post(
            "/api/1.0/photos/",
            data=json.dumps(
                dict(
                    image="unittest-post.jpg",
                    caption="UnitTest Post Caption",
                    takenBy="UnitTest Post Taken",
                    country="UnitTest Post Country",
                    countryCode="UT",
                    city="UnitTest Post City",
                    album="UnitTest Photo Album 1",
                    categories="UnitTest Category 1"
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        photo = Photos.query.filter_by(Image="unittest-post.jpg").first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=photo.PhotoID).first()
        albums = PhotoAlbums.query.filter_by(Title="UnitTest Photo Album 1").all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertEquals(1, len(albums))
        self.assertEquals(self.valid_albums[0], album.AlbumID)

    def test_adding_album_and_category_with_nonexisting_string(self):
        """When using a non-existing string, should add a new entry."""
        response = self.app.post(
            "/api/1.0/photos/",
            data=json.dumps(
                dict(
                    image="unittest-post.jpg",
                    caption="UnitTest Post Caption",
                    takenBy="UnitTest Post Taken",
                    country="UnitTest Post Country",
                    countryCode="UT",
                    city="UnitTest Post City",
                    album="UnitTest New Album",
                    categories="UnitTest New Category"
                )
            ),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())

        photo = Photos.query.filter_by(Image="unittest-post.jpg").first()
        album = PhotosAlbumsMapping.query.filter_by(PhotoID=photo.PhotoID).first()
        cat = PhotosCategoriesMapping.query.filter_by(PhotoID=photo.PhotoID).first()

        albums = PhotoAlbums.query.filter_by(Title="UnitTest New Album").all()
        cats = PhotoCategories.query.filter_by(Category="UnitTest New Category").all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertEquals(1, len(albums))
        self.assertEquals(1, len(cats))
        self.assertEquals(albums[0].AlbumID, album.AlbumID)
        self.assertEquals(cats[0].PhotoCategoryID, cat.PhotoCategoryID)
