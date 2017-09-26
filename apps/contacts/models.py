from app import db


class Contacts(db.Model):
    """Various pieces of data for the Contacts page."""
    __tablename__ = "Contacts"
    ContactsID = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(100), nullable=False)
    TechRider = db.Column(db.String(100))
    InputList = db.Column(db.String(100))
    Backline = db.Column(db.String(100))
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)
