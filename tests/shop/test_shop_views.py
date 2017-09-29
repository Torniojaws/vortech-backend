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
        db.session.add(logo1)
        db.session.add(logo2)
        db.session.add(logo3)
        db.session.commit()
        self.valid_logo_ids = [logo1.ShopItemLogoID, logo2.ShopItemLogoID, logo3.ShopItemLogoID]

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
        item2_cat2 = ShopItemsCategoriesMapping(
            ShopItemID=self.valid_items[1],
            ShopCategoryID=self.valid_cats[1]
        )
        db.session.add(item2_cat1)
        db.session.add(item2_cat2)
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

        self.assertEquals(2, len(data["shopItems"][0]["urls"]))
        self.assertEquals(
            [self.valid_cats[0], self.valid_cats[1]],
            data["shopItems"][0]["categories"]
        )
        self.assertEquals("Spotify", data["shopItems"][0]["urls"][0]["urlTitle"])
        self.assertEquals(
            "http://www.example.com/spotify",
            data["shopItems"][0]["urls"][0]["url"]
        )
        self.assertEquals(self.valid_logo_ids[0], data["shopItems"][0]["urls"][0]["logoID"])
