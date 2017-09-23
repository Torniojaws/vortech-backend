"""CFPS = Categories, Formats, People, Songs. They are quite complex, so they were implemented
separately for the POST /releases handling. Note that ALL of the functions here insert things into
their "standalone" tables. We also test the mapping."""

import unittest

from sqlalchemy import asc

from app import db
from apps.releases.add_cfps import add_categories
from apps.releases.models import Releases, ReleaseCategories, ReleasesCategoriesMapping
from apps.utils.time import get_datetime


class TestAddCategories(unittest.TestCase):
    def setUp(self):
        # The release we use for these tests
        release = Releases(
            Title="UnitTest",
            Date=get_datetime(),
            Artist="UnitTest Arts",
            Credits="UnitTest is a good and fun activity",
            Created=get_datetime(),
        )
        db.session.add(release)
        db.session.commit()
        self.release_id = release.ReleaseID

        # For testing the existing category ID
        cat = ReleaseCategories(
            ReleaseCategory="UnitTest"
        )
        db.session.add(cat)
        db.session.commit()
        self.existing_category_id = cat.ReleaseCategoryID

    def tearDown(self):
        cat = ReleaseCategories.query.filter(
            ReleaseCategories.ReleaseCategory.like("UnitTest%")
        ).all()
        for c in cat:
            db.session.delete(c)
        db.session.commit()

        release = Releases.query.filter_by(ReleaseID=self.release_id).first()
        db.session.delete(release)
        db.session.commit()

    def test_adding_categories_by_existing_id(self):
        """When using an existing category ID, no new entry should appear in ReleaseCategories
        table and the mapping should be added to ReleasesCategoriesMapping for this release."""
        add_categories(self.release_id, [self.existing_category_id])

        cats = ReleaseCategories.query.all()
        mapping = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(cats))
        self.assertEquals(1, len(mapping))
        self.assertEquals(self.existing_category_id, mapping[0].ReleaseCategoryID)

    def test_adding_categories_with_string_values(self):
        """When the values are strings, the will be inserted to ReleaseCategories as new entries.
        They should then be mapped to ReleasesCategoriesMapping for the current release."""
        categories = ["UnitTest Catastrophy", "UnitTest Category 5"]
        add_categories(self.release_id, categories)

        cats = ReleaseCategories.query.all()
        mapping = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_id).order_by(
            asc(ReleasesCategoriesMapping.ReleasesCategoriesMappingID)
        ).all()

        # Should be connected to the release
        cat1 = ReleaseCategories.query.filter_by(ReleaseCategory="UnitTest Catastrophy").first()
        cat2 = ReleaseCategories.query.filter_by(ReleaseCategory="UnitTest Category 5").first()

        self.assertEquals(3, len(cats))
        self.assertEquals(mapping[0].ReleaseCategoryID, cat1.ReleaseCategoryID)
        self.assertEquals(mapping[1].ReleaseCategoryID, cat2.ReleaseCategoryID)

    def test_adding_categories_with_existing_string(self):
        """When the category value is a string that exists in ReleaseCategories, then it should not
        be added as a new (duplicate) entry. We should reuse the ID for mapping to current release.
        """
        categories = ["UnitTest"]
        add_categories(self.release_id, categories)

        cats = ReleaseCategories.query.all()
        mapping = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(cats))
        self.assertEquals(cats[0].ReleaseCategoryID, mapping[0].ReleaseCategoryID)

    def test_adding_category_using_id_that_does_not_exist(self):
        """When using a numeric ID that does not exist in ReleaseCategories, we should skip it
        completely. No mapping should be added for current release."""
        add_categories(self.release_id, [0])

        cats = ReleaseCategories.query.all()
        mapping = ReleasesCategoriesMapping.query.filter_by(ReleaseID=self.release_id).first()

        self.assertEquals(1, len(cats))
        self.assertTrue(mapping is None)
