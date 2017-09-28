"""The Videos table models will be here."""

from app import db


class Videos(db.Model):
    """This contains the references to all video URLs"""
    __tablename__ = "Videos"
    VideoID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(200), nullable=False)
    URL = db.Column(db.Text, nullable=False)
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class VideoCategories(db.Model):
    """The values for valid video categories."""
    __tablename__ = "VideoCategories"
    VideoCategoryID = db.Column(db.Integer, primary_key=True)
    Category = db.Column(db.String(200), nullable=False)


class VideosCategoriesMapping(db.Model):
    """The mapping between Videos and the categories it is in."""
    __tablename__ = "VideosCategoriesMapping"
    VideosCategoriesMappingID = db.Column(db.Integer, primary_key=True)
    VideoID = db.Column(
        db.Integer, db.ForeignKey("Videos.VideoID", ondelete="CASCADE"), nullable=False
    )
    VideoCategoryID = db.Column(
        db.Integer, db.ForeignKey("VideoCategories.VideoCategoryID"), nullable=False
    )
