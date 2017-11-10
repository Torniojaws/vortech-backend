import json
import unittest

from app import app, db
from apps.downloads.models import DownloadsReleases
from apps.releases.models import Releases
from apps.utils.time import get_datetime


class TestDownloadsReleasesViews(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # Add 2 releases
        release1 = Releases(
            Title="UnitTest 1",
            Date=get_datetime(),
            Artist="UnitTest Arts 1",
            Credits="UnitTest is a good and fun activity",
            Created=get_datetime(),
            ReleaseCode="TEST001"
        )
        release2 = Releases(
            Title="UnitTest 2",
            Date=get_datetime(),
            Artist="UnitTest 2 Arts",
            Credits="UnitTest too is good for testing",
            Created=get_datetime(),
            ReleaseCode="TEST002"
        )
        db.session.add(release1)
        db.session.add(release2)
        db.session.commit()
        self.release_ids = [release1.ReleaseID, release2.ReleaseID]

        # Add downloads for them
        rel1_dl1 = DownloadsReleases(
            ReleaseID=self.release_ids[0],
            DownloadDate="2017-01-01 12:00:15"
        )
        rel1_dl2 = DownloadsReleases(
            ReleaseID=self.release_ids[0],
            DownloadDate="2017-01-02 12:00:15"
        )
        rel1_dl3 = DownloadsReleases(
            ReleaseID=self.release_ids[0],
            DownloadDate="2017-01-03 12:00:15"
        )
        rel2_dl1 = DownloadsReleases(
            ReleaseID=self.release_ids[1],
            DownloadDate="2017-03-02 01:00:15"
        )
        rel2_dl2 = DownloadsReleases(
            ReleaseID=self.release_ids[1],
            DownloadDate="2017-04-02 12:00:15"
        )
        db.session.add(rel1_dl1)
        db.session.add(rel1_dl2)
        db.session.add(rel1_dl3)
        db.session.add(rel2_dl1)
        db.session.add(rel2_dl2)
        db.session.commit()

    def tearDown(self):
        # Will also delete the downloads
        for release in Releases.query.filter(Releases.Title.like("UnitTest%")).all():
            db.session.delete(release)
        db.session.commit()

    def test_getting_all_download_counts(self):
        """Should return the download counts for all releases."""
        response = self.app.get("/api/1.0/downloads/releases/")
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(2, len(data["downloads"]))

        self.assertEquals(self.release_ids[0], data["downloads"][0]["releaseID"])
        self.assertEquals(3, data["downloads"][0]["count"])
        self.assertEquals("2017-01-01 12:00:15", data["downloads"][0]["since"])

        self.assertEquals(self.release_ids[1], data["downloads"][1]["releaseID"])
        self.assertEquals(2, data["downloads"][1]["count"])
        self.assertEquals("2017-03-02 01:00:15", data["downloads"][1]["since"])

    def test_getting_download_count_for_specific_release(self):
        """Should return the download count for the specified release."""
        response = self.app.get("/api/1.0/downloads/releases/{}".format(self.release_ids[1]))
        data = json.loads(response.data.decode())

        self.assertEquals(200, response.status_code)
        self.assertNotEquals(None, data)
        self.assertEquals(1, len(data["downloads"]))

        self.assertEquals(self.release_ids[1], data["downloads"][0]["releaseID"])
        self.assertEquals(2, data["downloads"][0]["count"])
        self.assertEquals("2017-03-02 01:00:15", data["downloads"][0]["since"])

    def test_adding_a_download(self):
        """Should add the entry to DB using the release ID specified in the JSON."""
        response = self.app.post(
            "/api/1.0/downloads/releases/",
            data=json.dumps(
                dict(
                    releaseID=self.release_ids[0],
                )
            ),
            content_type="application/json"
        )

        downloads = DownloadsReleases.query.filter_by(ReleaseID=self.release_ids[0]).all()

        self.assertEquals(201, response.status_code)
        self.assertTrue("Location" in response.data.decode())
        self.assertEquals(4, len(downloads))
