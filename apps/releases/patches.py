"""To implement the RFC 6902 logic for patches, there are some various complex methods needed.
For clarity, they are in this separate file as helper methods."""

from copy import deepcopy
from jsonpatch import JsonPatch

from app import db
from apps.releases.models import ReleasesCategoriesMapping, ReleasesFormatsMapping
from apps.releases.add_cfps import add_categories, add_formats, add_people, add_songs
from apps.people.models import ReleasesPeopleMapping
from apps.songs.models import ReleasesSongsMapping


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
    # TODO: How/Should we handle the multiple results from each mapping type?
    # But generally "op": "test" is only used once - it doesn't really make sense to use it many
    # times in one JSON anyway.
    return result


def patch_mapping(patch):
    """This is used to map a patch "path" or "from" to a custom value."""
    mapping = {
        "/title": "/Title",
        "/releaseDate": "/Date",
        "/artist": "/Artist",
        "/credits": "/Credits",
        "/categories": "/Categories",
        "/formats": "/Formats",
        "/people": "/People",
        "/songs": "/Songs",
    }

    mutable = deepcopy(patch)
    for prop in patch:
        if prop == "path" or prop == "from":
            mutable[prop] = mapping.get(patch[prop], None)
    return mutable


def patch_categories(patches, release_id):
    """Apply patches to ReleasesCategoriesMapping table. Since there are multiple rows, we need
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
            add_categories(release_id, patch["value"])
        elif patch["op"] == "copy":
            # This has no meaningful operation in Release Categories, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in Release Categories, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            ReleasesCategoriesMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the Release Categories case
            ReleasesCategoriesMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
            print("Releases patch_categories() got values: {}\n".format(patch["value"]))
            add_categories(release_id, patch["value"])


def patch_formats(patches, release_id):
    """Apply patches to ReleasesFormatsMapping table. Since there are multiple rows, we need
    some special processing for it, which the regular JsonPatch cannot handle."""
    # Filter out unrelated patches
    fmt_patches = [p for p in patches if "/Formats" in p.values()]

    for patch in fmt_patches:
        if patch["op"] == "add":
            # Generally it is a list of values, eg.
            # {"op": "add", "path": "/Formats", "value": [1, 2, "New"]}
            # Where 1 and 2 are references to existing ones, and "New" is a new format to add
            # also, non-array values are possible:
            # {"op": "add", "path": "/Formats", "value": "Another"}
            add_formats(release_id, patch["value"])
        elif patch["op"] == "copy":
            # This has no meaningful operation in Release Formats, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in Release Formats, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            ReleasesFormatsMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the Release Formats case
            ReleasesFormatsMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
            add_formats(release_id, patch["value"])


def patch_people(patches, release_id):
    """Apply patches to ReleasesPeopleMapping table. Since there are multiple rows, we need
    some special processing for it, which the regular JsonPatch cannot handle."""
    # Filter out unrelated patches
    people_patches = [p for p in patches if "/People" in p.values()]

    for patch in people_patches:
        if patch["op"] == "add":
            # Generally it is a list of values, eg.
            # {"op": "add", "path": "/People", "value": [{1: "Guitar", {"New": "Drums"}]}
            # Where 1 is a reference to an existing person, and "New" is a new person to add
            # also, non-array values are possible:
            # {"op": "add", "path": "/People", "value": {"New": "Bass"}}
            add_people(release_id, patch["value"])
        elif patch["op"] == "copy":
            # This has no meaningful operation in Release People, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in Release People, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            ReleasesPeopleMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the Release People case
            ReleasesPeopleMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
            add_people(release_id, patch["value"])


def patch_songs(patches, release_id):
    """Apply patches to ReleasesSongsMapping table. Since there are multiple rows, we need
    some special processing for it, which the regular JsonPatch cannot handle."""
    # Filter out unrelated patches
    song_patches = [p for p in patches if "/Songs" in p.values()]

    for patch in song_patches:
        if patch["op"] == "add":
            # Generally it is a list of values, eg.
            # {"op": "add", "path": "/Songs", "value": [{1: 123, {"New Song": 223}]}
            # Where 1 is a reference to an existing song, and "New" is a new song to add
            # also, non-array values are possible:
            # {"op": "add", "path": "/Songs", "value": {"New": 555}}
            add_songs(release_id, patch["value"])
        elif patch["op"] == "copy":
            # This has no meaningful operation in Release Songs, so not implemented.
            continue
        elif patch["op"] == "move":
            # This has no meaningful operation in Release Songs, so not implemented.
            continue
        elif patch["op"] == "remove":
            # NB "remove" is for deleting an entire resource.
            # To remove specific ID(s), use "replace".
            ReleasesSongsMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
        elif patch["op"] == "replace":
            # This is really a delete + insert operation in the Release People case
            ReleasesSongsMapping.query.filter_by(ReleaseID=release_id).delete()
            db.session.commit()
            add_songs(release_id, patch["value"])
