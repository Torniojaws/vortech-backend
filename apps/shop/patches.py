"""To implement the RFC 6902 logic for patches, there are some various complex methods needed.
For clarity, they are in this separate file as helper methods."""

from copy import deepcopy
from jsonpatch import JsonPatch


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

    data = item.asdict(exclude_pk=True, **kwargs)
    patch = JsonPatch(mapped_patchdata)
    data = patch.apply(data)
    item.fromdict(data)


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
        "/urlTitle": "/URLTitle",
        "/url": "/URL",
        "/logoID": "/LogoID",
    }

    mutable = deepcopy(patch)
    for prop in patch:
        if prop == "path" or prop == "from":
            mutable[prop] = mapping.get(patch[prop], None)
    return mutable
