from app import db


class Biography(db.Model):
    """Every time a new Biography is added, it becomes a new entry. We want to keep old entries
    for archival reasons. Technically they are not needed."""
    __tablename__ = "Biography"
    BiographyID = db.Column(db.Integer, primary_key=True)
    Short = db.Column(db.Text, nullable=False)
    Full = db.Column(db.Text, nullable=False)
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)
