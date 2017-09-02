from flask import Flask
from flask_autodoc import Autodoc

app = Flask(__name__)
auto = Autodoc(app)


@app.route("/")
@auto.doc()
def index():
    """This is the main entry point, ye landlubbers!"""
    return "Land ahoy!"


@app.route('/apidoc')
def documentation():
    """All routes will be documented automatically here"""
    return auto.html()


if __name__ == "__main__":
    app.run(host='0.0.0.0')
