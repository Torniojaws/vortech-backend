from app import db


class News(db.Model):
    """The basic data for news items"""
    __tablename__ = "News"
    NewsID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    Contents = db.Column(db.Text, nullable=False)
    Author = db.Column(db.String(255), nullable=False)
    Created = db.Column(db.DateTime, nullable=False)
    Updated = db.Column(db.DateTime)


class NewsCategories(db.Model):
    """Defines the display values for categories that can be selected for news."""
    __tablename__ = "NewsCategories"
    NewsCategoryID = db.Column(db.Integer, primary_key=True)
    Category = db.Column(db.String(255), nullable=False)


class NewsCategoriesMapping(db.Model):
    """The mapping between News items and NewsCategories"""
    __tablename__ = "NewsCategoriesMapping"
    NewsCategoriesMappingID = db.Column(db.Integer, primary_key=True)
    NewsID = db.Column(
        db.Integer, db.ForeignKey("News.NewsID", ondelete="CASCADE"), nullable=False
    )
    NewsCategoryID = db.Column(db.Integer, nullable=False)
