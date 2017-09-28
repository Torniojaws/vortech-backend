"""To implement the RFC 6902 logic for patches, there are some various complex methods needed.
For clarity, they are in this separate file as helper methods."""

from copy import deepcopy
from jsonpatch import JsonPatch

from app import db
from apps.videos.models import VideosCategoriesMapping
from apps.videos.add_categories import add_categories


def patch_item(video, patchdata, **kwargs):
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

    # Do not pass Categories patches in Videos patch JSON, to prevent an error due to categories
    # not being in Videos model.
    video_patches = [p for p in mapped_patchdata if "/Categories" not in p.values()]

    data = video.asdict(exclude_pk=True, **kwargs)
    patch = JsonPatch(video_patches)
    data = patch.apply(data)
    video.fromdict(data)

    # Apply category patches separately
    if [cat for cat in mapped_patchdata if "/Categories" in cat.values()]:
        patch_categories(mapped_patchdata, video.VideoID)


def patch_mapping(patch):
    """This is used to map a patch "path" or "from" to a custom value.
    Useful for when the patch path/from is not the same as the DB column name."""
    mapping = {
        "/title": "/Title",
        "/url": "/URL",
        "/categories": "/Categories"
    }

    mutable = deepcopy(patch)
    for prop in patch:
        if prop == "path" or prop == "from":
            mutable[prop] = mapping.get(patch[prop], None)
    return mutable


def patch_categories(patches, video_id):
    """Apply patches to VideosCategoriesMapping table. Since there are multiple rows, we need
    some special processing for it, which the regular JsonPatch cannot handle."""
    # Filter out unrelated patches
    cat_patches = [p for p in patches if "/Categories" in p.values()]

    for patch in cat_patches:
        if patch["op"] == "add":
            # Generally it is a list of values, eg.
            # {"op": "add", "path": "/Categories", "value": [1, 2, "New"]}
            # Where 1 and 2 are references to existing ones, and "New" is a new category to add
            # also, non-array values are possible:
            # {"op": "add", "path": "/Categories", "value": "Another"}
            add_categories(video_id, patch["value"])
        elif patch["op"] == "copy":
            # This has no meaningful operation in VIdeo Categories, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in Video Categories, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            VideosCategoriesMapping.query.filter_by(VideoID=video_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the Video Categories case
            VideosCategoriesMapping.query.filter_by(VideoID=video_id).delete()
            db.session.commit()
            add_categories(video_id, patch["value"])
