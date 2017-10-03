"""We want to share these two methods between the ShopItemsView class and also the Patch methods,
so they are implemented in a separate helper file here."""

from sqlalchemy import and_

from app import db
from apps.shop.models import ShopCategories, ShopItemsCategoriesMapping, ShopItemsURLMapping


def add_categories(item_id, categories):
    """Add categories for the given shopitem. Categories need to be checked. Integers should
    refer to existing Categories, which will refer to if they exist. Otherwise we skip the
    category. If the category is a string, we add it as new category, unless the string already
    exists."""
    for cat in categories:
        valid_category_id = None
        if type(cat) is int:
            # Possibly existing category
            exists = ShopCategories.query.filter_by(ShopCategoryID=cat).first()
            if exists:
                valid_category_id = exists.ShopCategoryID
            else:
                # Non-existing ID, skipping...
                print("")
                continue
        else:
            # New category, but let's check the name does not exist already
            # NB: The value should be a dict like {"category": "abc", "subcategory": "xyz"}
            exists = ShopCategories.query.filter(
                and_(
                    ShopCategories.Category == cat["category"],
                    ShopCategories.SubCategory == cat["subcategory"]
                )
            ).first()
            if exists:
                valid_category_id = exists.ShopCategoryID
            else:
                # Does not exist. Let's add it.
                new_cat = ShopCategories(
                    Category=cat["category"],
                    SubCategory=cat["subcategory"]
                )
                db.session.add(new_cat)
                db.session.commit()
                valid_category_id = new_cat.ShopCategoryID

        # Add the mapping
        mapping = ShopItemsCategoriesMapping(
            ShopItemID=item_id,
            ShopCategoryID=valid_category_id
        )
        db.session.add(mapping)
        db.session.commit()


def add_urls(item_id, urls):
    """Add URLs for the given shopitem. URLs do not need any check-up logic. We'll just insert
    the data as-is."""
    for url in urls:
        new_url = ShopItemsURLMapping(
            ShopItemID=item_id,
            URLTitle=url["title"],
            URL=url["url"],
            ShopItemLogoID=url["logoID"],
        )
        db.session.add(new_url)
    db.session.commit()
