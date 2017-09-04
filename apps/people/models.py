from app import db


class People(db.Model):
    """The people related to the band. Both members and guest artists."""
    __tablename__ = "People"
    PersonID = db.Column(db.Integer, primary_key=True)
    # Since we use utf8mb4, each character takes 4 bytes.
    # The max in InnoDB is 767 / 4 = 191 with rounding down.
    Name = db.Column(db.String(190), nullable=False, unique=True)


class ReleasesPeopleMapping(db.Model):
    """The mapping between Releases and People - who appeared on which release"""
    __tablename__ = "ReleasesPeopleMapping"
    ReleasesPeopleMappingID = db.Column(db.Integer, primary_key=True)
    ReleaseID = db.Column(
        db.Integer, db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"), nullable=False
    )
    PersonID = db.Column(
        db.Integer, db.ForeignKey("People.PersonID", ondelete="CASCADE"), nullable=False
    )
    Instruments = db.Column(db.String(500), nullable=False)
