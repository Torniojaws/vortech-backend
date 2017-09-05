from app import db


class Songs(db.Model):
    """All the songs the band has written"""
    __tablename__ = "Songs"
    SongID = db.Column(db.Integer, primary_key=True)
    # Since we use utf8mb4, each character takes 4 bytes.
    # The max for unique=True in InnoDB is then 767 / 4 = 191 with rounding down.
    Title = db.Column(db.String(190), nullable=False, unique=True)
    Duration = db.Column(db.Integer, nullable=False)


class ReleasesSongsMapping(db.Model):
    """The mapping between songs and releases"""
    __tablename__ = "ReleasesSongsMapping"
    ReleasesSongsMappingID = db.Column(db.Integer, primary_key=True)
    ReleaseID = db.Column(
        db.Integer, db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"), nullable=False
    )
    SongID = db.Column(
        db.Integer, db.ForeignKey("Songs.SongID", ondelete="CASCADE"), nullable=False
    )
