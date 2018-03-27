import importlib


def register_views(app):
    """All route views must be registered before they can be used"""
    api_path = "/api/1.0"

    from apps.biography.views import BiographyView
    BiographyView.register(app, route_base="{}/biography/".format(api_path))

    from apps.contacts.views import ContactsView
    ContactsView.register(app, route_base="{}/contacts/".format(api_path))

    from apps.downloads.views import DownloadsView
    DownloadsView.register(app, route_base="{}/downloads/".format(api_path))

    from apps.guestbook.views import GuestbookView
    GuestbookView.register(app, route_base="{}/guestbook/".format(api_path))

    from apps.news.views import NewsView
    NewsView.register(app, route_base="{}/news/".format(api_path))

    from apps.people.views import PeopleView
    PeopleView.register(app, route_base="{}/people/".format(api_path))

    from apps.photos.views import PhotosView
    PhotosView.register(app, route_base="{}/photos/".format(api_path))

    from apps.releases.views import ReleasesView
    ReleasesView.register(app, route_base="{}/releases/".format(api_path))

    from apps.shop.views import ShopItemsView
    ShopItemsView.register(app, route_base="{}/shopitems/".format(api_path))

    from apps.shows.views import ShowsView
    ShowsView.register(app, route_base="{}/shows/".format(api_path))

    from apps.songs.views import SongsView
    SongsView.register(app, route_base="{}/songs/".format(api_path))

    from apps.users.views import UsersView, UserLoginView, UserLogoutView, UserRefreshTokenView
    UsersView.register(app, route_base="{}/users/".format(api_path))
    UserLoginView.register(app, route_base="{}/login/".format(api_path))
    UserLogoutView.register(app, route_base="{}/logout/".format(api_path))
    UserRefreshTokenView.register(app, route_base="{}/refresh/".format(api_path))

    from apps.videos.views import VideosView
    VideosView.register(app, route_base="{}/videos/".format(api_path))

    from apps.visitors.views import VisitorsView
    VisitorsView.register(app, route_base="{}/visits/".format(api_path))

    from apps.votes.views import PhotosVotesView, ReleaseVotesView
    PhotosVotesView.register(app, route_base="{}/votes/photos/".format(api_path))
    ReleaseVotesView.register(app, route_base="{}/votes/releases/".format(api_path))


def register_models(app):
    """All database models need to be registered for Flask-Migrate to see them"""
    for model in [
        "biography",
        "contacts",
        "downloads",
        "guestbook",
        "news",
        "people",
        "photos",
        "releases",
        "shop",
        "shows",
        "songs",
        "users",
        "visitors",
        "votes",
    ]:
        mod = importlib.import_module(
            "apps.{}.models".format(model)
        )
    return mod
