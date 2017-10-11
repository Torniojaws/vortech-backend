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
    Created = db.Column(db.DateTime)