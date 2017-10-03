import json
import unittest

from app import app, db
from apps.shop.models import (
    ShopItems,
    ShopCategories,
    ShopItemsCategoriesMapping,
    ShopItemLogos,
    ShopItemsURLMapping
)
from apps.utils.time import get_datetime


class TestShopViews(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

        # Add some categories
        cat1 = ShopCategories(
            Category="Units",
            SubCategory="Tests"
        )
        cat2 = ShopCategories(
            Category="UnitTests",
            SubCategory="TestsUnits"
        )
        db.session.add(cat1)
        db.session.add(cat2)
        db.session.commit()
        self.valid_cats = [cat1.ShopCategoryID, cat2.ShopCategoryID]

        # And some 3rd party logos
        logo1 = ShopItemLogos(
            Image="unittest-spotify.jpg",
            Created=get_datetime()
        )
        logo2 = ShopItemLogos(
            Image="unittest-bandcamp.jpg",
            Created=get_datetime()
        )
        logo3 = ShopItemLogos(
            Image="unittest-amazon.jpg",
            Created=get_datetime()
        )
        logo4 = ShopItemLogos(
            Image="unittest-deezer.jpg",
            Created=get_datetime()
        )
        db.session.add(logo1)
        db.session.add(logo2)
        db.session.add(logo3)
        db.session.add(logo4)
        db.session.commit()
        self.valid_logo_ids = [
            logo1.ShopItemLogoID,
            logo2.ShopItemLogoID,
            logo3.ShopItemLogoID,
            logo4.ShopItemLogoID,
        ]

        # Add three shop items and related data
        item1 = ShopItems(
            Title="UnitTest ShopItem 1",
            Description="UnitTest This is item 1",
            Price=15.99,
            Currency="EUR",
            Image="unittest-shopitem1.jpg",
            Created=get_datetime()
        )
        db.session.add(item1)
        db.session.commit()
        self.valid_items = [item1.ShopItemID]

        item1_cat1 = ShopItemsCategoriesMapping(
            ShopItemID=self.valid_items[0],
            ShopCategoryID=self.valid_cats[0]
        )
        item1_cat2 = ShopItemsCategoriesMapping(
            ShopItemID=self.valid_items[0],
            ShopCategoryID=self.valid_cats[1]
        )
        db.session.add(item1_cat1)
        db.session.add(item1_cat2)
        db.session.commit()

        item1_url1 = ShopItemsURLMapping(
            ShopItemID=self.valid_items[0],
            URLTitle="Spotify",
            URL="http://www.example.com/spotify",
            ShopItemLogoID=self.valid_logo_ids[0]
        )
        item1_url2 = ShopItemsURLMapping(
            ShopItemID=self.valid_items[0],
            URLTitle="BandCamp",
            URL="http://www.example.com/bandcamp",
            ShopItemLogoID=self.valid_logo_ids[1]
        )
        db.session.add(item1_url1)
        db.session.add(item1_url2)
        db.session.commit()

        # Item 2
        item2 = ShopItems(
            Title="UnitTest ShopItem 2",
            Description="UnitTest This is item 2",
            Price=8.49,
            Currency="EUR",
            Image="unittest-shopitem2.jpg",
            Created=get_datetime()
        )
        db.session.add(item2)
        db.session.commit()
        self.valid_items.append(item2.ShopItemID)

        item2_cat1 = ShopItemsCategoriesMapping(
            ShopItemID=self.valid_items[1],
            ShopCategoryID=self.valid_cats[0]
        )
        db.session.add(item2_cat1)
        db.session.commit()

        item2_url1 = ShopItemsURLMapping(
            ShopItemID=self.valid_items[1],
            URLTitle="Spotify",
            URL="http://www.example.com/spotify",
            ShopItemLogoID=self.valid_logo_ids[0]
        )
        item2_url2 = ShopItemsURLMapping(
            ShopItemID=self.valid_items[1],
            URLTitle="BandCamp",
            URL="http://www.example.com/bandcamp",
            ShopItemLogoID=self.valid_logo_ids[1]
        )
        db.session.add(item2_url1)
        db.session.add(item2_url2)
        db.session.commit()

        # Item 3
        item3 = ShopItems(
            Title="UnitTest ShopItem 3",
            Description="UnitTest This is item 3",
            Price=12,
            Currency="EUR",
            Image="unittest-shopitem3.jpg",
            Created=get_datetime()
        )
        db.session.add(item3)
        db.session.commit()
        self.valid_items.append(item3.ShopItemID)

        item3_cat1 = ShopItemsCategoriesMapping(
            ShopItemID=self.valid_items[2],
            ShopCategoryID=self.valid_cats[0]
        )
        item3_cat2 = ShopItemsCategoriesMapping(
            ShopItemID=self.valid_items[2],
            ShopCategoryID=self.valid_cats[1]
        )
        db.session.add(item3_cat1)
        db.session.add(item3_cat2)
        db.session.commit()

        item3_url1 = ShopItemsURLMapping(
            ShopItemID=self.valid_items[2],
            URLTitle="Spotify",
            URL="http://www.example.com/spotify",
            ShopItemLogoID=self.valid_logo_ids[0]
        )
        item3_url2 = ShopItemsURLMapping(
            ShopItemID=self.valid_items[2],
            URLTitle="BandCamp",
            URL="http://www.example.com/bandcamp",
            ShopItemLogoID=self.valid_logo_ids[1]
        )
        db.session.add(item3_url1)
        db.session.add(item3_url2)
        db.session.commit()

    def tearDown(self):
        for cat in ShopCategories.query.filter(ShopCategories.Category.like("Unit%")).all():
            db.session.delete(cat)

        for logo in ShopItemLogos.query.filter(ShopItemLogos.Image.like("unittest%")).all():
            db.session.delete(logo)

        for item in ShopItems.query.filter(ShopItems.Title.like("UnitTest%")).all():
            db.session.delete(item)
        db.session.commit()

    def test_getting_all_shopitems(self):
        """This should return all the shopitems along with their associated data, in ascending
        order, ID=1 first."""
        response = self.app.get("/api/1.0/shopitems/")
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(3, len(data["shopItems"]))

        self.assertEquals("UnitTest ShopItem 1", data["shopItems"][0]["title"])
        self.assertEquals("UnitTest This is item 1", data["shopItems"][0]["description"])
        self.assertEquals(15.99, data["shopItems"][0]["price"])
        self.assertEquals("EUR", data["shopItems"][0]["currency"])
        self.assertEquals("unittest-shopitem1.jpg", data["shopItems"][0]["image"])
        self.assertNotEquals("", data["shopItems"][0]["createdAt"])
        self.assertTrue("updatedAt" in data["shopItems"][0])

        self.assertEquals(
            [self.valid_cats[0], self.valid_cats[1]],
            data["shopItems"][0]["categories"]
        )
        self.assertEquals(2, len(data["shopItems"][0]["urls"]))
        self.assertEquals("Spotify", data["shopItems"][0]["urls"][0]["urlTitle"])
        self.assertEquals(
            "http://www.example.com/spotify",
            data["shopItems"][0]["urls"][0]["url"]
        )
        self.assertEquals(self.valid_logo_ids[0], data["shopItems"][0]["urls"][0]["logoID"])

    def test_getting_specific_shopitem(self):
        """Should return the data of the specified shopitem."""
        response = self.app.get("/api/1.0/shopitems/{}".format(self.valid_items[2]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(data["shopItems"]))

        self.assertEquals("UnitTest ShopItem 3", data["shopItems"][0]["title"])
        self.assertEquals("UnitTest This is item 3", data["shopItems"][0]["description"])
        self.assertEquals(12, data["shopItems"][0]["price"])
        self.assertEquals("EUR", data["shopItems"][0]["currency"])
        self.assertEquals("unittest-shopitem3.jpg", data["shopItems"][0]["image"])
        self.assertNotEquals("", data["shopItems"][0]["createdAt"])
        self.assertTrue("updatedAt" in data["shopItems"][0])

        self.assertEquals(
            [self.valid_cats[0], self.valid_cats[1]],
            data["shopItems"][0]["categories"]
        )
        self.assertEquals(2, len(data["shopItems"][0]["urls"]))

        self.assertEquals("Spotify", data["shopItems"][0]["urls"][0]["urlTitle"])
        self.assertEquals(
            "http://www.example.com/spotify",
            data["shopItems"][0]["urls"][0]["url"]
        )
        self.assertEquals(self.valid_logo_ids[0], data["shopItems"][0]["urls"][0]["logoID"])

        self.assertEquals("BandCamp", data["shopItems"][0]["urls"][1]["urlTitle"])
        self.assertEquals(
            "http://www.example.com/bandcamp",
            data["shopItems"][0]["urls"][1]["url"]
        )
        self.assertEquals(self.valid_logo_ids[1], data["shopItems"][0]["urls"][1]["logoID"])

    def test_getting_shopitems_by_category(self):
        """Should return all items that match the subcategory."""
        response = self.app.get("/api/1.0/shopitems/category/{}/".format(self.valid_cats[1]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(2, len(data["shopItems"]))

        self.assertEquals("UnitTest ShopItem 1", data["shopItems"][0]["title"])
        self.assertEquals("UnitTest ShopItem 3", data["shopItems"][1]["title"])

    def test_adding_shopitem(self):
        """Should add the new item and its related data (categories and urls). For URLs, there is
        no valid case to reference any existing URLs in the database, so they will be added every
        time. However, we can reuse a logo (eg. Spotify), so basically you can pick a logo in the
        UI and then the POST data will have an ID."""
        response = self.app.post(
            "/api/1.0/shopitems/",
            data=json.dumps(
                dict(
                    title="UnitTest Post",
                    description="UnitTest Description",
                    price=14.95,
                    currency="EUR",
                    image="unittest-post.jpg",
                    categories=[
                        self.valid_cats[0],
                        {"category": "UnitTests", "subcategory": "UnitTest New Subcategory"}
                    ],
                    urls=[
                        {
                            "title": "Spotify",
                            "url": "http://www.example.com/spotify/1",
                            "logoID": self.valid_logo_ids[0]
                        },
                        {
                            "title": "Amazon",
                            "url": "http://www.example.com/amazon/123",
                            "logoID": self.valid_logo_ids[2]
                        },
                    ]
                )
            ),
            content_type="application/json"
        )
        data = response.data.decode()

        item = ShopItems.query.filter_by(Title="UnitTest Post").first_or_404()
        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=item.ShopItemID).all()
        urls = ShopItemsURLMapping.query.filter_by(ShopItemID=item.ShopItemID).all()

        new_cat = ShopCategories.query.filter_by(
            SubCategory="UnitTest New Subcategory").first()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)

        self.assertNotEquals(None, item)
        self.assertNotEquals(None, cats)
        self.assertNotEquals(None, urls)

        self.assertEquals("UnitTest Post", item.Title)
        self.assertEquals("UnitTest Description", item.Description)
        self.assertEquals(14.95, float(item.Price))
        self.assertEquals("EUR", item.Currency)
        self.assertEquals("unittest-post.jpg", item.Image)

        self.assertEquals(2, len(cats))
        self.assertEquals("UnitTests", new_cat.Category)
        self.assertEquals("UnitTest New Subcategory", new_cat.SubCategory)

        self.assertEquals(2, len(urls))
        # These appear in insert order. Sorting by title would be a lot of work for little benefit
        self.assertEquals("Spotify", urls[0].URLTitle)
        self.assertEquals("http://www.example.com/spotify/1", urls[0].URL)
        self.assertEquals("Amazon", urls[1].URLTitle)
        self.assertEquals("http://www.example.com/amazon/123", urls[1].URL)

    def test_updating_shop_item(self):
        """Should replace all existing values with the new updated values."""
        response = self.app.put(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                dict(
                    title="UnitTest Updated Title",
                    description="UnitTest Updated Description",
                    price=11.95,
                    currency="EUR",
                    image="unittest-update.jpg",
                    categories=[
                        self.valid_cats[0],
                        self.valid_cats[1],
                        {"category": "UnitTests", "subcategory": "UnitTest New Subcategory"}
                    ],
                    urls=[
                        {
                            "title": "Spotify",
                            "url": "http://www.example.com/spotify/2",
                            "logoID": self.valid_logo_ids[0]
                        },
                        {
                            "title": "Amazon MP3",
                            "url": "http://www.example.com/amazon/124",
                            "logoID": self.valid_logo_ids[2]
                        },
                        {
                            "title": "BandCamp",
                            "url": "http://www.example.com/bandcamp/987",
                            "logoID": self.valid_logo_ids[2]
                        },
                    ]
                )
            ),
            content_type="application/json"
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals("", response.data.decode())

        item = ShopItems.query.filter_by(ShopItemID=self.valid_items[1]).first_or_404()
        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()
        urls = ShopItemsURLMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()

        new_cat = ShopCategories.query.filter_by(
            SubCategory="UnitTest New Subcategory").first()

        self.assertNotEquals(None, item)
        self.assertNotEquals(None, cats)
        self.assertNotEquals(None, urls)

        self.assertEquals("UnitTest Updated Title", item.Title)
        self.assertEquals("UnitTest Updated Description", item.Description)
        self.assertEquals(11.95, float(item.Price))
        self.assertEquals("EUR", item.Currency)
        self.assertEquals("unittest-update.jpg", item.Image)
        self.assertNotEquals("", item.Updated)

        self.assertEquals(3, len(cats))
        self.assertEquals("UnitTests", new_cat.Category)
        self.assertEquals("UnitTest New Subcategory", new_cat.SubCategory)

        self.assertEquals(3, len(urls))
        # These appear in insert order. Sorting by title would be a lot of work for little benefit
        self.assertEquals("Spotify", urls[0].URLTitle)
        self.assertEquals("http://www.example.com/spotify/2", urls[0].URL)
        self.assertEquals("Amazon MP3", urls[1].URLTitle)
        self.assertEquals("http://www.example.com/amazon/124", urls[1].URL)
        self.assertEquals("BandCamp", urls[2].URLTitle)
        self.assertEquals("http://www.example.com/bandcamp/987", urls[2].URL)

    def test_patching_shopitem_add(self):
        """Patch a ShopItems entry with "add" operation."""
        response = self.app.patch(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "add",
                        "path": "/title",
                        "value": "UnitTest Patched Title"
                    }),
                    dict({
                        "op": "add",
                        "path": "/categories",
                        "value": [self.valid_cats[1]]
                    }),
                    dict({
                        "op": "add",
                        "path": "/urls",
                        "value": [
                            {
                                "title": "Deezer",
                                "url": "deezer.com",
                                "logoID": self.valid_logo_ids[3]
                            }
                        ]
                    }),
                ]
            ),
            content_type="application/json"
        )

        item = ShopItems.query.filter_by(ShopItemID=self.valid_items[1]).first_or_404()
        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()
        urls = ShopItemsURLMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        self.assertEquals("UnitTest Patched Title", item.Title)
        self.assertEquals(2, len(cats))
        self.assertEquals(3, len(urls))
        self.assertEquals("Deezer", urls[2].URLTitle)
        self.assertEquals("deezer.com", urls[2].URL)

    def test_patching_shopitem_copy(self):
        """Patch a ShopItems entry with "copy" operation. There is no possible copy operation for
        categories and urls. Trying to do it would throw JsonPatchConflict since you can only copy
        to the same resource, ie. on top of itself."""
        response = self.app.patch(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/title",
                        "path": "/description"
                    })
                ]
            ),
            content_type="application/json"
        )

        item = ShopItems.query.filter_by(ShopItemID=self.valid_items[1]).first_or_404()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals("UnitTest ShopItem 2", item.Description)

    def test_patching_shopitem_move(self):
        """Patch a ShopItems entry with "move" operation. Move will by definition empty the source
        resource and populate the target resource with the value from source. However, this does
        not currently work yet due to SQLAlchemy and JSONPatch incompatibility. Just the value is
        replaced. The correct behaviour will be implemented later on."""
        response = self.app.patch(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "move",
                        "from": "/description",
                        "path": "/image"
                    })
                ]
            ),
            content_type="application/json"
        )

        item = ShopItems.query.filter_by(ShopItemID=self.valid_items[1]).first_or_404()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals("UnitTest This is item 2", item.Image)

    def test_patching_shopitem_remove(self):
        """Patch a ShopItems entry with "remove" operation. This does not work for the base object
        due to SQLAlchemy JSONPatch incompatibility. But it does work for the joined tables URLs
        and categories."""
        response = self.app.patch(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "remove",
                        "path": "/title"
                    }),
                    dict({
                        "op": "remove",
                        "path": "/categories"
                    }),
                    dict({
                        "op": "remove",
                        "path": "/urls"
                    })
                ]
            ),
            content_type="application/json"
        )

        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()
        urls = ShopItemsURLMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals([], cats)
        self.assertEquals([], urls)

    def test_patching_shopitem_replace(self):
        """Patch a ShopItems entry with "replace" operation."""
        response = self.app.patch(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "replace",
                        "path": "/title",
                        "value": "UnitTest Patched Title"
                    }),
                    dict({
                        "op": "replace",
                        "path": "/categories",
                        "value": [self.valid_cats[1]]
                    }),
                    dict({
                        "op": "replace",
                        "path": "/urls",
                        "value": [
                            {
                                "title": "Deezer",
                                "url": "deezer.com",
                                "logoID": self.valid_logo_ids[3]
                            }
                        ]
                    }),
                ]
            ),
            content_type="application/json"
        )

        item = ShopItems.query.filter_by(ShopItemID=self.valid_items[1]).first_or_404()
        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()
        urls = ShopItemsURLMapping.query.filter_by(ShopItemID=self.valid_items[1]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

        self.assertEquals("UnitTest Patched Title", item.Title)
        self.assertEquals(1, len(cats))
        self.assertEquals(1, len(urls))
        self.assertEquals("Deezer", urls[0].URLTitle)
        self.assertEquals("deezer.com", urls[0].URL)

    def test_deleting_shop_item(self):
        """Should delete the specified shop item and it's mappings."""
        response = self.app.delete("/api/1.0/shopitems/{}".format(self.valid_items[2]))

        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=self.valid_items[2]).all()
        urls = ShopItemsURLMapping.query.filter_by(ShopItemID=self.valid_items[2]).all()

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
        self.assertEquals([], cats)
        self.assertEquals([], urls)

    def test_invalid_category_id(self):
        """When an invalid category ID is given, it should be skipped."""
        response = self.app.post(
            "/api/1.0/shopitems/",
            data=json.dumps(
                dict(
                    title="UnitTest Post",
                    description="UnitTest Description",
                    price=14.95,
                    currency="EUR",
                    image="unittest-post.jpg",
                    categories=[0],
                    urls=[
                        {
                            "title": "Spotify",
                            "url": "http://www.example.com/spotify/1",
                            "logoID": self.valid_logo_ids[0]
                        }
                    ]
                )
            ),
            content_type="application/json"
        )
        data = response.data.decode()

        item = ShopItems.query.filter_by(Title="UnitTest Post").first_or_404()
        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=item.ShopItemID).all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertEquals([], cats)

    def test_existing_string_category(self):
        """Should use the existing category and not create a new entry to ShopCategories."""
        response = self.app.post(
            "/api/1.0/shopitems/",
            data=json.dumps(
                dict(
                    title="UnitTest Post",
                    description="UnitTest Description",
                    price=14.95,
                    currency="EUR",
                    image="unittest-post.jpg",
                    categories=[
                        {
                            "category": "UnitTests",
                            "subcategory": "TestsUnits"
                        }
                    ],
                    urls=[
                        {
                            "title": "Spotify",
                            "url": "http://www.example.com/spotify/1",
                            "logoID": self.valid_logo_ids[0]
                        }
                    ]
                )
            ),
            content_type="application/json"
        )
        data = response.data.decode()

        item = ShopItems.query.filter_by(Title="UnitTest Post").first_or_404()
        cats = ShopItemsCategoriesMapping.query.filter_by(ShopItemID=item.ShopItemID).all()
        category_entries = ShopCategories.query.filter_by(Category="UnitTests").all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in data)
        self.assertEquals(1, len(cats))
        # Should only have one entry for the given values.
        self.assertEquals(1, len(category_entries))

    def test_patching_categories(self):
        """Patch ShopItems categories with "copy" and "move" operations. There is no possible
        operation for categories and urls. Trying to do it would throw JsonPatchConflict since you
        can only copy to the same resource, ie. on top of itself."""
        response = self.app.patch(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/categories",
                        "path": "/categories"
                    }),
                    dict({
                        "op": "move",
                        "from": "/categories",
                        "path": "/categories"
                    })
                ]
            ),
            content_type="application/json"
        )

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())

    def test_patching_urls(self):
        """Patch ShopItems urls with "copy" and "move" operations. There is no possible
        operation for categories and urls. Trying to do it would throw JsonPatchConflict since you
        can only copy to the same resource, ie. on top of itself."""
        response = self.app.patch(
            "/api/1.0/shopitems/{}".format(self.valid_items[1]),
            data=json.dumps(
                [
                    dict({
                        "op": "copy",
                        "from": "/urls",
                        "path": "/urls"
                    }),
                    dict({
                        "op": "move",
                        "from": "/urls",
                        "path": "/urls"
                    })
                ]
            ),
            content_type="application/json"
        )

        self.assertEquals(204, response.status_code)
        self.assertEquals("", response.data.decode())
