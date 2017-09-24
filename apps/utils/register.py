import importlib


def register_views(app):
    """All route views must be registered before the can be used"""
    api_path = "/api/1.0"

    from apps.biography.views import BiographyView
    BiographyView.register(app, route_base="{}/biography/".format(api_path))

    from apps.news.views import NewsView
    NewsView.register(app, route_base="{}/news/".format(api_path))

    from apps.releases.views import ReleasesView
    ReleasesView.register(app, route_base="{}/releases/".format(api_path))

    from apps.shows.views import ShowsView
    ShowsView.register(app, route_base="{}/shows/".format(api_path))

    from apps.songs.views import SongsView
    SongsView.register(app, route_base="{}/songs/".format(api_path))

    from apps.users.views import UsersView
    UsersView.register(app, route_base="{}/users/".format(api_path))


def register_models(app):
    """All database models need to be registered for Flask-Migrate to see them"""
    for model in [
        "biography",
        "news",
        "people",
        "releases",
        "shows",
        "songs",
        "users",
    ]:
        mod = importlib.import_module(
            "apps.{}.models".format(model)
        )
    return mod
