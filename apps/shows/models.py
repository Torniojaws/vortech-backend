from app import db


class Shows(db.Model):
    """All the shows the band has done"""
    __tablename__ = "Shows"
    ShowID = db.Column(db.Integer, primary_key=True)
    ShowDate = db.Column(db.DateTime, nullable=False)
    CountryCode = db.Column(db.String(2), nullable=False)
    Country = db.Column(db.String(100), nullable=False)
    City = db.Column(db.String(100), nullable=False)
    Venue = db.Column(db.String(200))


class ShowsSongsMapping(db.Model):
    """The setlist mapping between Shows and Songs. Includes the Show-specific song order."""
    __tablename__ = "ShowsSongsMapping"
    SetlistID = db.Column(db.Integer, primary_key=True)
    ShowID = db.Column(
        db.Integer, db.ForeignKey("Shows.ShowID", ondelete="CASCADE"), nullable=False
    )
    SongID = db.Column(
        db.Integer, db.ForeignKey("Songs.SongID", ondelete="CASCADE"), nullable=False
    )
    SetlistOrder = db.Column(db.Integer)
    ShowSongDuration = db.Column(db.Integer)


class ShowsOtherBands(db.Model):
    """The list of bands that appeared in a given show, mapped to ShowID."""
    __tablename__ = "ShowsOtherBands"
    ShowsOtherBandsID = db.Column(db.Integer, primary_key=True)
    ShowID = db.Column(
        db.Integer, db.ForeignKey("Shows.ShowID", ondelete="CASCADE"), nullable=False
    )
    BandName = db.Column(db.String(200), nullable=False)
    BandWebsite = db.Column(db.Text)


class ShowsPeopleMapping(db.Model):
    """The mapping between Shows and People, to tell who played on which show and which
    instrument they used."""
    __tablename__ = "ShowsPeopleMapping"
    ShowsPeopleMappingID = db.Column(db.Integer, primary_key=True)
    ShowID = db.Column(
        db.Integer, db.ForeignKey("Shows.ShowID", ondelete="CASCADE"), nullable=False
    )
    PersonID = db.Column(
        db.Integer, db.ForeignKey("People.PersonID", ondelete="CASCADE"), nullable=False
    )
    Instruments = db.Column(db.String(500), nullable=False)
