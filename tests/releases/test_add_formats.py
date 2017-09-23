"""CFPS = Categories, Formats, People, Songs. They are quite complex, so they were implemented
separately for the POST /releases handling. Note that ALL of the functions here insert things into
their "standalone" tables. We also test the mapping."""

import unittest

from sqlalchemy import asc

from app import db
from apps.releases.add_cfps import add_formats
from apps.releases.models import Releases, ReleaseFormats, ReleasesFormatsMapping
from apps.utils.time import get_datetime


class TestAddFormats(unittest.TestCase):
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

        # For testing existing formats
        f = ReleaseFormats(
            Title="UnitTestFormat"
        )
        db.session.add(f)
        db.session.commit()
        self.existing_format_id = f.ReleaseFormatID

    def tearDown(self):
        formats = ReleaseFormats.query.filter(
            ReleaseFormats.Title.like("UnitTest%")
        ).all()
        for f in formats:
            db.session.delete(f)
        db.session.commit()

        release = Releases.query.filter_by(ReleaseID=self.release_id).first()
        db.session.delete(release)
        db.session.commit()

    def test_adding_formats_by_existing_id(self):
        """When using an existing ID, no new entries should appear in ReleaseFormats and the
        mapping for the current release should be correct."""
        add_formats(self.release_id, [self.existing_format_id])

        f = ReleaseFormats.query.all()
        mapping = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(f))
        self.assertEquals(1, len(mapping))
        self.assertEquals(self.existing_format_id, mapping[0].ReleaseFormatID)

    def test_adding_formats_with_new_string_values(self):
        """Should create a new entry and then do the mapping for current release."""
        formats = ["UnitTest Format C", "UnitTest Formulas Fatal"]
        add_formats(self.release_id, formats)

        f = ReleaseFormats.query.all()
        mapping = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_id).order_by(
            asc(ReleasesFormatsMapping.ReleaseFormatsMappingID)
        ).all()

        # Should be connected to the release
        f1 = ReleaseFormats.query.filter_by(Title="UnitTest Format C").first()
        f2 = ReleaseFormats.query.filter_by(Title="UnitTest Formulas Fatal").first()

        self.assertEquals(3, len(f))
        self.assertFalse(f1 is None)
        self.assertFalse(f2 is None)
        self.assertEquals(mapping[0].ReleaseFormatID, f1.ReleaseFormatID)
        self.assertEquals(mapping[1].ReleaseFormatID, f2.ReleaseFormatID)

    def test_adding_formats_with_existing_string_values(self):
        """Should not add a new entry and the mapping should be correct for current release."""
        formats = ["UnitTestFormat"]
        add_formats(self.release_id, formats)

        f = ReleaseFormats.query.all()
        mapping = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_id).all()

        self.assertEquals(1, len(f))
        self.assertEquals(f[0].ReleaseFormatID, mapping[0].ReleaseFormatID)

    def test_adding_formats_with_nonexisting_ids(self):
        """When you add format IDs that do not exist, no mapping should happen and no new entries
        should appear in ReleaseFormats."""
        add_formats(self.release_id, [0])

        f = ReleaseFormats.query.all()
        mapping = ReleasesFormatsMapping.query.filter_by(ReleaseID=self.release_id).first()

        self.assertEquals(1, len(f))
        self.assertTrue(mapping is None)
