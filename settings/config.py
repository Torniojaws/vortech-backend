from os.path import abspath, dirname, join
import configparser

# All the configs are in secret.cfg that must be created in prod server when deploying
CURRENT_DIR = abspath(dirname(__file__))
configfile = configparser.ConfigParser()
configpath = abspath(join(CURRENT_DIR, "secret.cfg"))
with open(configpath, "r") as cfg:
    configfile.read_file(cfg)


def database_uri(env):
    """Return the URI, which is used to connect to a specific server/database."""
    return (
        "{dialect}+{driver}://{user}:{password}@{host}:{port}/{database}?charset={charset}"
    ).format(
        dialect=configfile.get("database", "dialect"),
        driver=configfile.get("database", "driver"),
        user=configfile.get("database", "username"),
        password=configfile.get("database", "password"),
        host=configfile.get("database", "host"),
        port=configfile.get("database", "port"),
        database=configfile.get("database", "database"),
        charset=configfile.get("database", "charset"),
    )


class Config(object):
    """This will be the main configuration class, which will be used all around the app.
    The way to use it is to import CONFIG from this module, and then use it like:
    key = CONFIG.SECRET_KEY
    """
    SECRET_KEY = configfile.get("env", "secret")
    SQLALCHEMY_DATABASE_URI = database_uri(configfile.get("env", "env"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGPATH = configfile.get("log", "path")
    MIN_PASSWORD_LENGTH = 8
    # User access levels. These must match the DB table UsersAccessLevels
    GUEST_LEVEL = 1
    REGISTERED_LEVEL = 2
    MODERATOR_LEVEL = 3
    ADMIN_LEVEL = 4


class ProdConfig(Config):
    SQLALCHEMY_ECHO = False


class DevConfig(Config):
    SQLALCHEMY_ECHO = False


ENV = configfile.get("env", "env")

if ENV == "prod":
    CONFIG = ProdConfig
else:
    CONFIG = DevConfig
