from app import db


class Users(db.Model):
    """All users' information is stored here"""
    __tablename__ = "Users"
    UserID = db.Column(db.Integer(), primary_key=True)
    Name = db.Column(db.String(200), nullable=False)
    Email = db.Column(db.String(200))
    Username = db.Column(db.String(200), nullable=False)
    Password = db.Column(db.Text, nullable=False)
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
    UserID = db.Column(db.Integer, nullable=False)
    UsersAccessLevelID = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["fk_useraccess", "fk_useraccess_level"],
            ["Users.UserID", "UsersAccessLevels.UsersAccessLevelID"],
            ondelete="CASCADE"
        )
    )
