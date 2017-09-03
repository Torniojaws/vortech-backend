import importlib


def register_views(app):
    """All route views must be registered before the can be used"""
    api_path = "/api/1.0"

    from apps.news.views import NewsView
    NewsView.register(app, route_base="{}/news/".format(api_path))

    from apps.users.views import UsersView
    UsersView.register(app, route_base="{}/users/".format(api_path))


def register_models(app):
    """All database models need to be registered for Flask-Migrate to see them"""
    for model in [
        "news",
        "users",
    ]:
        mod = importlib.import_module(
            "apps.{}.models".format(model)
        )
    return mod
