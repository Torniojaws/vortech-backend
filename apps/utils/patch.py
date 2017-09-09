"""This implements the IETF-defined PATCH logic: https://tools.ietf.org/html/rfc6902 in an abstract
manner. The point is to extend this class for the Model-specific implementations, where we might
need to update multiple different Models.

The RFC 6902 defines a Patch JSON like this:
[
    { "op": "test", "path": "/a/b/c", "value": "foo" },
    { "op": "remove", "path": "/a/b/c" },
    { "op": "add", "path": "/a/b/c", "value": [ "foo", "bar" ] },
    { "op": "replace", "path": "/a/b/c", "value": 42 },
    { "op": "move", "from": "/a/b/c", "path": "/a/b/d" },
    { "op": "copy", "from": "/a/b/d", "path": "/a/b/e" }
]
"""
import abc
from app import db

# TODO: Delete this if jsonpatch works well


class Patch(metaclass=abc.ABCMeta):
    def __init__(self, target_id):
        self.id = target_id
        self.db = db

    def with_data(self, patchdict):
        """Run the patches defined in <patchdict>"""
        for patch in patchdict:
            # One row, eg. { "op": "remove", "path": "/a/b/c" }
            op = patch["op"]
            path = patch["path"]
            source = patch["from"] or None
            values = patch["value"] or None
            self.run(op, path, source, values)

    def run(self, op, path, source, values):
        switcher = {
            "add": self.add(path, values),
            "copy": self.copy(source, path),
            "move": self.move(source, path),
            "remove": self.remove(path),
            "replace": self.replace(path, values),
            "test": self.test(path, values),
        }
        return switcher.get(op, "Unknown operation, skipping...")

    @abc.abstractmethod
    def add(self, path, values):
        # Example:
        # PATCH /news/123
        # { "op": "add", "path": "/title", "value": "Edited news title" }
        # Add the value(s) to the given path. The path should be created if it does not exist.
        # If there already is a value in "path", it will be replaced.
        raise NotImplementedError("You must define add(path, values) method")

    @abc.abstractmethod
    def copy(self, source, path):
        # Example:
        # PATCH /news/123
        # { "op": "copy", "from": "/author", "path": "/news/123/creator" }
        # Basically just copies an existing value to another path.
        # The new value will replace any existing value.
        raise NotImplementedError("You must define copy(source, path) method")

    @abc.abstractmethod
    def move(self, source, path):
        # Example:
        # PATCH /news/123
        # { "op": "move", "from": "/news/123/title", "path": "/news/123/header" }
        # Delete the original value, and add it to the new path.
        raise NotImplementedError("You must define move(source, path) method")

    @abc.abstractmethod
    def remove(self, path):
        # Example:
        # PATCH /news/123
        # { "op": "remove", "path": "/news/123/contents" }
        # Deletes the value.
        raise NotImplementedError("You must define remove(path) method")

    @abc.abstractmethod
    def replace(self, path, values):
        # Example:
        # PATCH /news/123
        # { "op": "replace", "path": "/news/123/title", "value": "New title" }
        # Replace an existing value in an existing path with the new value given.
        raise NotImplementedError("You must define replace(path, values) method")

    @abc.abstractmethod
    def test(self, path, values):
        # Example:
        # PATCH /news/123
        # { "op": "test", "path": "/a/b/c", "value": "foo" }
        # Compare the value in the path to the value provided in the request.
        # Return a boolean response
        raise NotImplementedError("You must define test(path, values) method")

    @abc.abstractmethod
    def get_column(self, path):
        """The path in the JSON might be eg. "/email" while the database column name could be for
        example "EmailAddress", so we need to map them in the implementation classes."""
        raise NotImplementedError("You must define get_column(path) method")
