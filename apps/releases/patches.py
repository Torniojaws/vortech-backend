"""To implement the RFC 6902 logic for patches, there are some various complex methods needed.
For clarity, they are in this separate file as helper methods."""

from copy import deepcopy
from jsonpatch import JsonPatch

from app import db
from apps.releases.models import (
    ReleasesCategoriesMapping,
    ReleasesFormatsMapping,
    ReleasesPeopleMapping,
    ReleasesSongsMapping,
)


def patch_item(release, patchdata, **kwargs):
    """Sequentially runs the patches defined in the JSON."""
    result = None
    # Map the values to DB column names
    mapped_patchdata = []
    for p in patchdata:
        # Replace eg. /title with /Title
        p = patch_mapping(p)
        mapped_patchdata.append(p)

    # Prevent a KeyError for the mapping models by using a separate list for Releases table
    separate_values = ["/Categories", "/Formats", "/People", "/Songs"]
    release_patches = mapped_patchdata
    for separate in separate_values:
        release_patches = [rp for rp in release_patches if separate not in rp.values()]

    data = release.asdict(exclude_pk=True, **kwargs)
    patch = JsonPatch(release_patches)
    data = patch.apply(data)
    release.fromdict(data)

    # If the patches contain Category patches, run them.
    if [cat for cat in mapped_patchdata if "/Categories" in cat.values()]:
        result = patch_categories(mapped_patchdata, release.ReleaseID)

    # If the patches contain Format patches, run them.
    if [fmt for fmt in mapped_patchdata if "/Formats" in fmt.values()]:
        result = patch_formats(mapped_patchdata, release.ReleaseID)

    # If the patches contain People patches, run them.
    if [pe for pe in mapped_patchdata if "/People" in pe.values()]:
        result = patch_people(mapped_patchdata, release.ReleaseID)

    # If the patches contain Song patches, run them.
    if [s for s in mapped_patchdata if "/Songs" in s.values()]:
        result = patch_songs(mapped_patchdata, release.ReleaseID)

    # We only return from non-Release patches. It is None if no test ops were in the patches.
    return result


def patch_mapping(patch):
    """This is used to map a patch "path" or "from" to a custom value.
    Useful for when the patch path/from is not the same as the DB column name. Eg.

    PATCH /news/123
    [
        { "op": "move", "from": "/title", "path": "/author" }
    ]

    If the News column in the DB is "Title", using the lowercase "/title" in the patch would fail
    because the case does not match, and MariaDB is case-sensitive in Linux. So the mapping
    converts this:
        { "op": "move", "from": "/title", "path": "/author" }
    To this:
        { "op": "move", "from": "/Title", "path": "/Author" }
    """
    mapping = {
        "/title": "/Title",
        "/contents": "/Contents",
        "/author": "/Author",
        "/updated": "/Updated",
        "/categories": "/NewsCategoryID",
    }

    mutable = deepcopy(patch)
    for prop in patch:
        if prop == "path" or prop == "from":
            mutable[prop] = mapping.get(patch[prop], None)
    return mutable


def patch_categories(patches, news_id):
    """Apply patches to NewsCategoriesMapping table. Since there are multiple rows, we need some
    special processing for it, which the regular JsonPatch cannot handle.

    Generally we receive a patch like this:
        {"op": "add", "path": "/NewsCategoryID", "value": [2, 3]}
    or:
        {"op": "replace", "path": "/NewsCategoryID", "value": [4, 5]}

    We only return values for the "test" ops, which must return boolean. The spec doesn't seem to
    tell what to do if there are multiple "test" ops. So for now, we return False if there's any
    non-matches.
    """
    # Filter out unrelated patches
    cat_patches = [p for p in patches if "/NewsCategoryID" in p.values()]

    for patch in cat_patches:
        if patch["op"] == "add":
            # Generally it is a list of values
            for value in patch["value"]:
                new_category = NewsCategoriesMapping(
                    NewsID=news_id,
                    NewsCategoryID=value,
                )
                db.session.add(new_category)
            db.session.commit()
        elif patch["op"] == "copy":
            # This has no meaningful operation in News Categories, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in News Categories, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            NewsCategoriesMapping.query.filter_by(NewsID=news_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the News Categories case
            NewsCategoriesMapping.query.filter_by(NewsID=news_id).delete()
            db.session.commit()
            for value in patch["value"]:
                new_category = NewsCategoriesMapping(
                    NewsID=news_id,
                    NewsCategoryID=value,
                )
                db.session.add(new_category)
            db.session.commit()
