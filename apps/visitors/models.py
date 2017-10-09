from app import db


class Visitors(db.Model):
    """All the visits will be stored here with some extra information used for statistics."""
    __tablename__ = "Visitors"
    VisitID = db.Column(db.Integer, primary_key=True)
    VisitDate = db.Column(db.DateTime, nullable=False)
    IPAddress = db.Column(db.String(20))
    Continent = db.Column(db.String(20))
    Country = db.Column(db.String(40))
