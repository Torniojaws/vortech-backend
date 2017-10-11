from app import db


class DownloadsReleases(db.Model):
    """All downloads of releases will be counted here."""
    __tablename__ = "DownloadsReleases"
    DownloadID = db.Column(db.Integer, primary_key=True)
    ReleaseID = db.Column(
        db.Integer,
        db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"),
        nullable=False
    )
    DownloadDate = db.Column(db.DateTime, nullable=False)
