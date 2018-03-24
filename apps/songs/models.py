from app import db


class Songs(db.Model):
    """All the songs the band has written"""
    __tablename__ = "Songs"
    SongID = db.Column(db.Integer, primary_key=True)
    # Since we use utf8mb4, each character takes 4 bytes.
    # The max for unique=True in InnoDB is then 767 / 4 = 191 with rounding down.
    Title = db.Column(db.String(190), nullable=False, unique=True)
    Duration = db.Column(db.Integer, nullable=False)


class ReleasesSongsMapping(db.Model):
    """The mapping between songs and releases. There is also a release-specific duration for
    songs. For example if the song is of different length on a live album than in the studio
    album. We also want to keep a duration in Songs, so that one-off songs that are not on any
    releases can also have a duration."""
    __tablename__ = "ReleasesSongsMapping"
    ReleasesSongsMappingID = db.Column(db.Integer, primary_key=True)
    ReleaseID = db.Column(
        db.Integer, db.ForeignKey("Releases.ReleaseID", ondelete="CASCADE"), nullable=False
    )
    SongID = db.Column(
        db.Integer, db.ForeignKey("Songs.SongID", ondelete="CASCADE"), nullable=False
    )
    ReleaseSongDuration = db.Column(db.Integer, nullable=False)


class SongsLyrics(db.Model):
    """The lyrics for songs are stored here. The songs are referred to by the SongID. They are
    expected to be stored with line breaks included. Eg. 'Song lyrics<br/>Some lyric<br/><br/>'"""
    __tablename__ = "SongsLyrics"
    SongsLyricsID = db.Column(db.Integer, primary_key=True)
    Lyrics = db.Column(db.Text, nullable=False)
    Author = db.Column(db.String(190), nullable=False)
    SongID = db.Column(
        db.Integer, db.ForeignKey("Songs.SongID", ondelete="CASCADE"), nullable=False
    )


class SongsTabs(db.Model):
    """The tabs for songs are stored here. The tabs are referred to by the SongID. The actual tabs
    are stored as static files on the server, under static/tabs/filename.ext, which we refer to in
    the database entries. One song can have multiple tabs, for example a TXT file and a GP5 file.
    Each file will have its own entry in this table.

    The title is used by the frontend as the link text and is the tab type, eg. 'Guitar Pro 5'.
    The song title will be taken from the FK reference.

    The filename refers to just the tab filename, and does not contain the path to it, so it is
    eg. 'song-tab.gp5'
    """
    __tablename__ = "SongsTabs"
    SongsTabsID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(100), nullable=False)
    Filename = db.Column(db.String(150), nullable=False)
    SongID = db.Column(
        db.Integer, db.ForeignKey("Songs.SongID", ondelete="CASCADE"), nullable=False
    )
