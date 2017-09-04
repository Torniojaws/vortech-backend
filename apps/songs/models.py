from app import db


class Songs(db.Model):
    """All the songs the band has written"""
    __tablename__ = "Songs"
    SongID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False, unique=True)
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
