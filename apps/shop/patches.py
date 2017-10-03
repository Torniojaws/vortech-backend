"""To implement the RFC 6902 logic for patches, there are some various complex methods needed.
For clarity, they are in this separate file as helper methods."""

from copy import deepcopy
from jsonpatch import JsonPatch

from app import db
from apps.shop.add_cu import add_categories, add_urls
from apps.shop.models import ShopItemsCategoriesMapping, ShopItemsURLMapping


def patch_item(item, patchdata, **kwargs):
    """This is used to run patches on the database model, using the method described here:
    https://gist.github.com/mattupstate/d63caa0156b3d2bdfcdb

    NB: There are two limitations:
    1. When op is "move", there is no simple way to make sure the source is empty
    2. When op is "remove", there also is no simple way to make sure the source is empty

    Most of the data in this project is nullable=False anyway, so they cannot be deleted.
    """
    # Map the values to DB column names
    mapped_patchdata = []
    for p in patchdata:
        # Replace eg. /title with /Title
        p = patch_mapping(p)
        mapped_patchdata.append(p)

    # Remove categories and urls from the base object set, to prevent non-existent object error
    patches = [s for s in mapped_patchdata if "/Categories" not in s.values()]
    shop_patches = [s for s in patches if "/URLs" not in s.values()]

    data = item.asdict(exclude_pk=True, **kwargs)
    patch = JsonPatch(shop_patches)
    data = patch.apply(data)
    item.fromdict(data)
    db.session.commit()

    # Patch categories, if any
    if [cat for cat in mapped_patchdata if "/Categories" in cat.values()]:
        patch_categories(item.ShopItemID, mapped_patchdata)

    # Patch URLs, if any
    if [url for url in mapped_patchdata if "/URLs" in url.values()]:
        patch_urls(item.ShopItemID, mapped_patchdata)


def patch_mapping(patch):
    """This is used to map a patch "path" or "from" to a custom value.
    Useful for when the patch path/from is not the same as the DB column name."""
    mapping = {
        "/title": "/Title",
        "/description": "/Description",
        "/price": "/Price",
        "/currency": "/Currency",
        "/image": "/Image",
        "/categories": "/Categories",
        "/urls": "/URLs",
    }

    mutable = deepcopy(patch)
    for prop in patch:
        if prop == "path" or prop == "from":
            mutable[prop] = mapping.get(patch[prop], None)
    return mutable


def patch_categories(item_id, patches):
    """Patch the categories based on the instructions."""
    # Filter out unrelated patches
    cat_patches = [p for p in patches if "/Categories" in p.values()]

    for patch in cat_patches:
        if patch["op"] == "add":
            # Generally it is a list of values, eg.
            # {"op": "add", "path": "/Categories", "value": [1, 2, "New"]}
            # Where 1 and 2 are references to existing ones, and "New" is a new category to add
            # also, non-array values are possible:
            # {"op": "add", "path": "/Categories", "value": "Another"}
            add_categories(item_id, patch["value"])
        elif patch["op"] == "copy":
            # This has no meaningful operation in VIdeo Categories, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in Video Categories, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            ShopItemsCategoriesMapping.query.filter_by(ShopItemID=item_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the Video Categories case
            ShopItemsCategoriesMapping.query.filter_by(ShopItemID=item_id).delete()
            db.session.commit()
            add_categories(item_id, patch["value"])


def patch_urls(item_id, patches):
    """Patch the URLs based on the instructions."""
    # Filter out unrelated patches
    url_patches = [p for p in patches if "/URLs" in p.values()]

    for patch in url_patches:
        if patch["op"] == "add":
            # Generally it is a list of dicts, eg.
            # {"op": "add", "path": "/URLs", "value": [{}, {}]}
            # Where 1 and 2 are references to existing ones, and "New" is a new url to add
            add_urls(item_id, patch["value"])
        elif patch["op"] == "copy":
            # This has no meaningful operation in Shopitem URLs, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in Shopitem URLs, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            ShopItemsURLMapping.query.filter_by(ShopItemID=item_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the Video Categories case
            ShopItemsURLMapping.query.filter_by(ShopItemID=item_id).delete()
            db.session.commit()
            add_urls(item_id, patch["value"])
