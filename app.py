from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from apps.utils.register import register_views, register_models
from settings.config import CONFIG

app = Flask(__name__)
app.config.from_object(CONFIG)
# Otherwise you will get a 404 if you open eg. site.com/path, when it is defined as site.com/path/
app.url_map.strict_slashes = False
db = SQLAlchemy(app)
CORS(app)

# Register all database models for Flask-Migrate
register_models(app)

# Register all views for Flask
register_views(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
