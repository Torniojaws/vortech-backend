"""This will feature many different Votes models as we add more things to vote, like Photos or
merchandise."""

from app import db


class VotesReleases(db.Model):
    """All votes for releases are in this model."""
    __tablename__ = "VotesReleases"
    VoteID = db.Column(db.Integer, primary_key=True)
    ReleaseID = db.Column(
        db.Integer,
        db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"),
        nullable=False
    )
    Vote = db.Column(
        db.Float(precision=2, asdecimal=True, decimal_return_scale=2),
        nullable=False
    )
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class VotesPhotos(db.Model):
    """All votes for photos are in this model."""
    __tablename__ = "VotesPhotos"
    VoteID = db.Column(db.Integer, primary_key=True)
    PhotoID = db.Column(
        db.Integer,
        db.ForeignKey("Photos.PhotoID", ondelete="CASCADE"),
        nullable=False
    )
    Vote = db.Column(
        db.Float(precision=2, asdecimal=True, decimal_return_scale=2),
        nullable=False
    )
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class VotesSongs(db.Model):
    """All votes for songs are in this model."""
    __tablename__ = "VotesSongs"
    VoteID = db.Column(db.Integer, primary_key=True)
    SongID = db.Column(
        db.Integer,
        db.ForeignKey("Songs.SongID", ondelete="CASCADE"),
        nullable=False
    )
    Vote = db.Column(
        db.Float(precision=2, asdecimal=True, decimal_return_scale=2),
        nullable=False
    )
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)
