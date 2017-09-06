"""This is the News-specific extended Patch class"""
from apps.utils.patch import Patch


class Patch(Patch):
    def add(self, path, values):
        # Example:
        # PATCH /news/123
        # { "op": "add", "path": "/title", "value": "Edited news title" }
        # Add the value(s) to the given path. The path should be created if it does not exist.
        # If there already is a value in "path", it will be replaced.
        pass

    def copy(self, source, path):
        # Example:
        # PATCH /news/123
        # { "op": "copy", "from": "/author", "path": "/news/123/creator" }
        # Basically just copies an existing value to another path.
        # The new value will replace any existing value.
        pass

    def move(self, source, path):
        # Example:
        # PATCH /news/123
        # { "op": "move", "from": "/news/123/title", "path": "/news/123/header" }
        # Delete the original value, and add it to the new path.
        pass

    def remove(self, path):
        # Example:
        # PATCH /news/123
        # { "op": "remove", "path": "/news/123/contents" }
        # Deletes the value.
        pass

    def replace(self, path, values):
        # Example:
        # PATCH /news/123
        # { "op": "replace", "path": "/news/123/title", "value": "New title" }
        # Replace an existing value in an existing path with the new value given.
        pass

    def test(self, path, values):
        # Example:
        # PATCH /news/123
        # { "op": "test", "path": "/a/b/c", "value": "foo" }
        # Compare the value in the path to the value provided in the request.
        # Return a boolean response
        pass
