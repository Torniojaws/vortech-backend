from flask import Flask
from flask_autodoc import Autodoc
from flask_sqlalchemy import SQLAlchemy
from settings.config import CONFIG

import importlib

app = Flask(__name__)
auto = Autodoc(app)
app.config.from_object(CONFIG)
db = SQLAlchemy(app)


# Register all database models for Flask-Migrate
for model in [
    "news",
    "users",
]:
    mod = importlib.import_module(
        "apps.{}.models".format(model)
    )


@app.route("/")
@auto.doc()
def index():
    """This is the main entry point, ye landlubbers!"""
    return "Land ahoy!"


@app.route("/apidoc")
def documentation():
    """All routes will be documented automatically here"""
    return auto.html()


if __name__ == "__main__":
    app.run(host='0.0.0.0')
