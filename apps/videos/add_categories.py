from app import db
from apps.videos.models import VideosCategoriesMapping, VideoCategories


def add_categories(video_id, categories):
    """Insert the given categories for the current video. If the category value is a string,
    add it as a new category entry if it does not exist yet."""
    # This allows non-list values to be processed, eg. "value": "somevalue"
    if type(categories) is not list:
        categories = [categories]

    for category in categories:
        video_category_id = None
        if type(category) is int:
            # Possibly existing category
            exists = VideoCategories.query.filter_by(VideoCategoryID=category).first()
            if exists:
                video_category_id = exists.VideoCategoryID
            else:
                # The ID is invalid, and we don't want to add a category with a number as name
                print("")
                continue
        else:
            # String category - add it as a new category, if there is no existing category with
            # the same name
            exists = VideoCategories.query.filter_by(Category=category).first()
            if exists:
                video_category_id = exists.VideoCategoryID
            else:
                # Does not exist, let's add the new category
                new_category = VideoCategories(
                    Category=category
                )
                db.session.add(new_category)
                db.session.commit()
                video_category_id = new_category.VideoCategoryID

        # Now that we have a valid VideoCategoryID, we can map it to the current VideoID
        mapping = VideosCategoriesMapping(
            VideoID=video_id,
            VideoCategoryID=video_category_id
        )
        db.session.add(mapping)
        db.session.commit()
