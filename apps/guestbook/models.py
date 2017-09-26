from app import db


class Guestbook(db.Model):
    """All guestbook posts will be here. If UserID=1, then it is a guest user = not logged in.
    If a given name exists for a registered user, then a guest user cannot post using that name.
    The validation happens in the frontend, but we'll also have a ironclad check in the backend."""
    __tablename__ = "Guestbook"
    GuestbookID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    Author = db.Column(db.String(100), nullable=False)
    Message = db.Column(db.Text, nullable=False)
    AdminComment = db.Column(db.Text)
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)
