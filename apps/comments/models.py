"""This will feature many different Comment models as we add more things to comment on,
like Releases, Photos or ShopItems."""

from app import db


class CommentsNews(db.Model):
    """All comments for news are in this model."""
    __tablename__ = "CommentsNews"
    CommentID = db.Column(db.Integer, primary_key=True)
    NewsID = db.Column(
        db.Integer,
        db.ForeignKey("News.NewsID", ondelete="CASCADE"),
        nullable=False
    )
    Comment = db.Column(db.Text, nullable=False)
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class CommentsPhotos(db.Model):
    """All comments for photos are in this model."""
    __tablename__ = "CommentsPhotos"
    CommentID = db.Column(db.Integer, primary_key=True)
    PhotoID = db.Column(
        db.Integer,
        db.ForeignKey("Photos.PhotoID", ondelete="CASCADE"),
        nullable=False
    )
    Comment = db.Column(db.Text, nullable=False)
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class CommentsReleases(db.Model):
    """All comments for releases are in this model."""
    __tablename__ = "CommentsReleases"
    CommentID = db.Column(db.Integer, primary_key=True)
    ReleaseID = db.Column(
        db.Integer,
        db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"),
        nullable=False
    )
    Comment = db.Column(db.Text, nullable=False)
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class CommentsShopItems(db.Model):
    """All comments for shopitems are in this model."""
    __tablename__ = "CommentsShopItems"
    CommentID = db.Column(db.Integer, primary_key=True)
    ShopItemID = db.Column(
        db.Integer,
        db.ForeignKey("ShopItems.ShopItemID", ondelete="CASCADE"),
        nullable=False
    )
    Comment = db.Column(db.Text, nullable=False)
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class CommentsShows(db.Model):
    """All comments for shows are in this model."""
    __tablename__ = "CommentsShows"
    CommentID = db.Column(db.Integer, primary_key=True)
    ShowID = db.Column(
        db.Integer,
        db.ForeignKey("Shows.ShowID", ondelete="CASCADE"),
        nullable=False
    )
    Comment = db.Column(db.Text, nullable=False)
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class CommentsSongs(db.Model):
    """All comments for songs are in this model."""
    __tablename__ = "CommentsSongs"
    CommentID = db.Column(db.Integer, primary_key=True)
    SongID = db.Column(
        db.Integer,
        db.ForeignKey("Songs.SongID", ondelete="CASCADE"),
        nullable=False
    )
    Comment = db.Column(db.Text, nullable=False)
    UserID = db.Column(
        db.Integer,
        db.ForeignKey("Users.UserID", ondelete="CASCADE"),
        nullable=False
    )
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)
