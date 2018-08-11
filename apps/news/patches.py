"""Re-implemented JSON Patch for the News endpoint.

Valid payload example:
[
    {"op": "add", "path": "/title", "value": "something"},
    {"op": "remove", "path": "/author"},
    {"op": "replace", "path": "/categories", "value": [1, 2, 5]},
    {"op": "move", "from": "/contents", "path": "/author"},
    {"op": "copy", "from": "/title", "path": "/contents"},
    {"op": "test", "path": "/title", "value": "Hello"}
]

Remember that any "test" failure should reject the entire JSON
Add will append to arrays and objects, and will replace strings with the new value
Remove and move sets to NULL, unless DB constraint prevents it (In News, EVERYTHING is NOT NULL)
"""
import json

from typing import List

from app import db

from apps.news.models import News, NewsCategoriesMapping
from apps.utils.time import get_datetime


def patch_item(news_id, patches):
    """Apply the patches to the given news ID. If the categories change, they will be updated
    in the related NewsCategoriesMapping. Returns the modified JSON presentation."""
    news = News.query.filter_by(NewsID=news_id).first()
    result = {}

    # Make sure it is a list
    if not isinstance(patches, List):
        # Probably a JSON string
        patches = json.loads(patches)

    try:
        for patch in patches:
            # The RFC spec tells to return an object that has all the modifications
            result = apply_patch(news, patch, result)
    except ValueError as ve:
        # Invalid "op" in the patch. Cancel.
        print("ERROR! Invalid OP in patch:\n{}".format(ve))
        db.session.rollback()
        return {"success": False, "message": "Invalid operation in patch"}
    except AssertionError:
        # Test "op" did not pass the comparison. Cancel.
        print("ERROR! TEST did not match comparison in patch")
        db.session.rollback()
        return {"success": False, "message": "Comparison test failed in the patch"}
    except TypeError:
        # When passing non-array to categories
        print("Only lists are allowed in categories")
        db.session.rollback()
        return {"success": False, "message": "Only lists are allowed in categories"}
    except Exception as e:
        print("ERROR! General error - will rollback")
        print(e)
        # Any unknown error should also cancel the entire patch
        db.session.rollback()
        return {"success": False, "message": str(e)}

    news.Updated = get_datetime()
    db.session.commit()
    return result


def apply_patch(news, patch, result):
    """Process a single patch, eg. {"op": "add", "path": "/contents", "value": "Hi"}"""
    test_result = None

    if patch["op"] == "add":
        result = add(news, patch["path"], patch["value"], result)
    elif patch["op"] == "copy":
        result = copy(news, patch["from"], patch["path"], result)
    elif patch["op"] == "move":
        result = move(news, patch["from"], patch["path"], result)
    elif patch["op"] == "remove":
        result = remove(news, patch["path"], result)
    elif patch["op"] == "replace":
        result = replace(news, patch["path"], patch["value"], result)
    elif patch["op"] == "test":
        test_result = test(news, patch["path"], patch["value"])
        if test_result is False:
            raise AssertionError("Test operation did not pass - cancelling patch")
    else:
        raise ValueError("Unknown patch operation - cancelling patch and rolling back")

    if not test_result:
        news.Updated = get_datetime()
    return result


def add(news, target, value, result):
    """If target is a string, the original value is replaced with the new value.
    If target is an array or object, the new value is appended."""
    if target == "/categories":
        if isinstance(value, List):
            for cat in value:
                new_cats = NewsCategoriesMapping(
                    NewsID=news.NewsID,
                    NewsCategoryID=int(cat)
                )
                db.session.add(new_cats)

            final_cats = NewsCategoriesMapping.query.filter_by(NewsID=news.NewsID).all()
            result["categories"] = [ncatid.NewsCategoryID for ncatid in final_cats]
            # TODO: How about string values? Eg. possibly new categories (could be existing too)
        else:
            raise ValueError("Categories must be an array")
    else:
        if target == "/title":
            news.Title = value
            result["title"] = value
        if target == "/contents":
            news.Contents = value
            result["contents"] = value
        if target == "/author":
            news.Author = value
            result["author"] = value
    db.session.add(news)
    return result


def copy(news, source, target, result):
    """Copy value from source into target."""
    if target == "/categories":
        raise ValueError("Copying to categories is not allowed")
    else:
        news, result = update_values(news, source, target, result)
        db.session.add(news)
    return result


def move(news, source, target, result):
    """Copy the source value into target, and nullify source. Only if DB schema allows."""
    if target == "/categories":
        raise Exception("Moving to categories is not allowed")
    if source in ["/title", "/contents", "/author", "/created"]:
        raise Exception("The defined source cannot be nullified (NOT NULL)")
    if source == "/updated":
        news, result = update_values(news, source, target, result)
        news.Updated = None
        db.session.add(news)
    return result


def remove(news, target, result):
    """Nullify the value in target - but only if is allowed by DB schema. That is, only
    categories and updated."""
    if target == "/categories":
        for cat in NewsCategoriesMapping.query.filter_by(NewsID=news.NewsID).all():
            db.session.delete(cat)
        result["categories"] = []
    elif target == "/updated":
        news.Updated = None
        result["updated"] = None
        db.session.add(news)
    else:
        raise ValueError("Target cannot be removed due to constraints - cancelling")
    return result


def replace(news, target, value, result):
    """Replace the existing value in target with the new value, regardless of type."""
    if target == "/categories":
        if isinstance(value, List):
            for cat in NewsCategoriesMapping.query.filter_by(NewsID=news.NewsID).all():
                db.session.delete(cat)
            for new_cat in value:
                # TODO: Support strings?
                category = NewsCategoriesMapping(
                    NewsID=news.NewsID,
                    NewsCategoryID=new_cat
                )
                db.session.add(category)
            result["categories"] = value
        else:
            raise ValueError("Invalid categories type - must be a list (array)")
    else:
        news, result = update_values(news, None, target, result, value)
    db.session.add(news)
    return result


def test(news, target, value):
    """Compare the given value against the existing value in target. If they match, the test
    passes. If they do not match, the test fails and the ENTIRE patch should be cancelled. Any
    changes in the earlier steps of the current patch must be rolled back."""
    if target == "/title":
        return news.Title == value
    elif target == "/contents":
        return news.Contents == value
    elif target == "/author":
        return news.Author == value
    elif target == "/created":
        return news.Created.strftime("%Y-%m-%d %H:%M:%S") == value
    elif target == "/updated":
        return news.Updated.strftime("%Y-%m-%d %H:%M:%S") == value
    else:
        return False


def get_value(news, source):
    """Read the value source has in the DB."""
    if source == "/title":
        return news.Title
    if source == "/contents":
        return news.Contents
    if source == "/author":
        return news.Author
    if source == "/created":
        return news.Created.strftime("%Y-%m-%d %H:%M:%S")
    if source == "/updated":
        return news.Updated.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def update_values(news, source, target, result, direct_value=None):
    if direct_value:
        value = direct_value
    else:
        value = get_value(news, source)

    if target == "/title":
        news.Title = value
        result["title"] = value
    elif target == "/contents":
        news.Contents = value
        result["contents"] = value
    elif target == "/author":
        news.Author = value
        result["author"] = value
    elif target == "/created":
        news.Created = value
        result["created"] = value
    elif target == "/updated":
        news.Updated = value
        result["updated"] = value
    else:
        raise ValueError("Unknown target defined!")
    return news, result
