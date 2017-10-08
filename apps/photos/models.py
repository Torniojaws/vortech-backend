from app import db


class Photos(db.Model):
    """The primary data of all photos is stored here."""
    __tablename__ = "Photos"
    PhotoID = db.Column(db.Integer, primary_key=True)
    Image = db.Column(db.String(255), nullable=False)
    Caption = db.Column(db.Text)
    TakenBy = db.Column(db.String(200))
    Country = db.Column(db.String(100))
    CountryCode = db.Column(db.String(2))
    City = db.Column(db.String(100))
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class PhotoAlbums(db.Model):
    """Data related to specific photo albums is stored here."""
    __tablename__ = "PhotoAlbums"
    AlbumID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(200), nullable=False)
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class PhotosAlbumsMapping(db.Model):
    """The mapping between photos and albums."""
    __tablename__ = "PhotosAlbumsMapping"
    PhotosAlbumsMappingID = db.Column(db.Integer, primary_key=True)
    PhotoID = db.Column(
        db.Integer, db.ForeignKey("Photos.PhotoID", ondelete="CASCADE")
    )
    AlbumID = db.Column(
        db.Integer, db.ForeignKey("PhotoAlbums.AlbumID", ondelete="CASCADE")
    )


class PhotoCategories(db.Model):
    """All available photo categories are defined here."""
    __tablename__ = "PhotoCategories"
    PhotoCategoryID = db.Column(db.Integer, primary_key=True)
    Category = db.Column(db.String(200), nullable=False)


class PhotosCategoriesMapping(db.Model):
    """The mapping between photos and categories."""
    __tablename__ = "PhotosCategoriesMapping"
    PhotosCategoriesMappingID = db.Column(db.Integer, primary_key=True)
    PhotoID = db.Column(
        db.Integer, db.ForeignKey("Photos.PhotoID", ondelete="CASCADE")
    )
    PhotoCategoryID = db.Column(
        db.Integer, db.ForeignKey("PhotoCategories.PhotoCategoryID", ondelete="CASCADE")
    )
