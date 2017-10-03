from app import db


class ShopItems(db.Model):
    """The main data for all shop items."""
    __tablename__ = "ShopItems"
    ShopItemID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.Text)
    Price = db.Column(
        db.Float(precision=10, asdecimal=True, decimal_return_scale=2), nullable=False
    )
    Currency = db.Column(db.String(3), nullable=False)
    Image = db.Column(db.String(200))
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class ShopCategories(db.Model):
    """The categories that shop items can be in. Subcategories are eg.
    "t-shirt" or "live album", where the main category is eg.
    "clothing" or "release"."""
    __tablename__ = "ShopCategories"
    ShopCategoryID = db.Column(db.Integer, primary_key=True)
    Category = db.Column(db.String(200), nullable=False)
    SubCategory = db.Column(db.String(200), nullable=False)


class ShopItemsCategoriesMapping(db.Model):
    """The mapping between categories and shopitems."""
    __tablename__ = "ShopItemsCategoriesMapping"
    ShopItemsCategoriesMappingID = db.Column(db.Integer, primary_key=True)
    ShopItemID = db.Column(
        db.Integer, db.ForeignKey("ShopItems.ShopItemID", ondelete="CASCADE"), nullable=False
    )
    ShopCategoryID = db.Column(
        db.Integer,
        db.ForeignKey("ShopCategories.ShopCategoryID", ondelete="CASCADE"),
        nullable=False
    )


class ShopItemLogos(db.Model):
    """These are the references to 3rd party logos, like BandCamp, Spotify, etc."""
    __tablename__ = "ShopItemsLogos"
    ShopItemLogoID = db.Column(db.Integer, primary_key=True)
    Image = db.Column(db.String(200), nullable=False)
    Created = db.Column(db.DateTime)
    Updated = db.Column(db.DateTime)


class ShopItemsURLMapping(db.Model):
    """A given shopitem can have several URLs, for example to Amazon, BandCamp, or any other online
    service where it is for sale too. The mapping is here. One row per one URL and each can have
    one logo associated with it."""
    __tablename__ = "ShopItemsURLMapping"
    ShopItemsURLMappingID = db.Column(db.Integer, primary_key=True)
    ShopItemID = db.Column(
        db.Integer, db.ForeignKey("ShopItems.ShopItemID", ondelete="CASCADE"), nullable=False
    )
    URLTitle = db.Column(db.String(200), nullable=False)
    URL = db.Column(db.Text, nullable=False)
    ShopItemLogoID = db.Column(
        db.Integer, db.ForeignKey("ShopItemsLogos.ShopItemLogoID", ondelete="CASCADE")
    )
