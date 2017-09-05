from app import db


class Releases(db.Model):
    """The basic data for release items"""
    __tablename__ = "Releases"
    ReleaseID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(200), nullable=False)
    Date = db.Column(db.DateTime, nullable=False)
    Artist = db.Column(db.String(200), nullable=False)
    Credits = db.Column(db.Text)
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class ReleaseFormats(db.Model):
    """Release formats are the mediums they were released as, eg. "CD" or "Digital" etc."""
    __tablename__ = "ReleaseFormats"
    ReleaseFormatID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)


class ReleasesFormatsMapping(db.Model):
    """The mapping between Releases and ReleaseFormats"""
    __tablename__ = "ReleasesFormatsMapping"
    ReleaseFormatsMappingID = db.Column(db.Integer, primary_key=True)
    ReleaseFormatID = db.Column(
        db.Integer,
        db.ForeignKey("ReleaseFormats.ReleaseFormatID", ondelete="CASCADE"),
        nullable=False
    )
    ReleaseID = db.Column(
        db.Integer,
        db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"),
        nullable=False
    )


class ReleaseCategories(db.Model):
    """Release categories are for example "Full length", "Live album", "Demo", etc."""
    __tablename__ = "ReleaseCategories"
    ReleaseCategoryID = db.Column(db.Integer, primary_key=True)
    ReleaseCategory = db.Column(db.String(200))


class ReleasesCategoriesMapping(db.Model):
    """The mapping between Releases and their categories"""
    __tablename__ = "ReleasesCategoriesMapping"
    ReleasesCategoriesMappingID = db.Column(db.Integer, primary_key=True)
    ReleaseID = db.Column(
        db.Integer, db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"), nullable=False
    )
    ReleaseCategoryID = db.Column(
        db.Integer,
        db.ForeignKey("ReleaseCategories.ReleaseCategoryID", ondelete="CASCADE"),
        nullable=False
    )
