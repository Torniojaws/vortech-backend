from sqlalchemy.sql import expression

from app import db


class Users(db.Model):
    """All users' information is stored here"""
    __tablename__ = "Users"
    UserID = db.Column(db.Integer(), primary_key=True)
    Name = db.Column(db.String(50), nullable=False, unique=True)
    Email = db.Column(db.String(100), unique=True)
    Username = db.Column(db.String(50), nullable=False, unique=True)
    Password = db.Column(db.Text, nullable=False)
    # We use a default value of "False", ie. no one is subscribed automatically
    Subscriber = db.Column(
        db.Boolean, nullable=False, server_default=expression.false()
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class UsersAccessLevels(db.Model):
    """This defines the various access levels users can have"""
    __tablename__ = "UsersAccessLevels"
    UsersAccessLevelID = db.Column(db.Integer, primary_key=True)
    LevelName = db.Column(db.String(100), nullable=False)
    AccessDescription = db.Column(db.Text)


class UsersAccessMapping(db.Model):
    """Each users' access level is defined here"""
    __tablename__ = "UsersAccessMapping"
    UsersAccessMappingID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(
        db.Integer, db.ForeignKey("Users.UserID", ondelete="CASCADE"), nullable=False
    )
    UsersAccessLevelID = db.Column(
        db.Integer,
        db.ForeignKey("UsersAccessLevels.UsersAccessLevelID", ondelete="CASCADE"),
        nullable=False
    )


class UsersAccessTokens(db.Model):
    """User session access data is stored here."""
    __tablename__ = "UsersAccessTokens"
    UsersAccessTokenID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    AccessToken = db.Column(db.String(40))
    RefreshToken = db.Column(db.String(40))
    ExpirationDate = db.Column(db.DateTime, nullable=False)
