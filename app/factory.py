"""Flask application factory for dependency injection and testability."""

import logging
import os
import warnings

from flask import Flask
from flask_assets import Bundle, Environment
from flask_caching import Cache

from app.modules.testsupport import is_test_environment

logger = logging.getLogger(__name__)


def create_app(
    config=None,
    layout=None,
    bookmark_manager=None,
    link_tracker=None,
    testing=False,
):
    """
    Application factory for Flask app.

    Args:
        config: Optional config dict to override defaults
        layout: Optional Layout instance (for testing)
        bookmark_manager: Optional BookmarkManager instance (for testing)
        link_tracker: Optional LinkTracker instance (for testing)
        testing: If True, skip production initialization

    Returns:
        Configured Flask application
    """
    # Silence Flask-Caching warnings
    warnings.filterwarnings(
        "ignore",
        message=r"Flask-Caching: CACHE_TYPE is set to null.*",
        category=UserWarning,
    )
    logging.getLogger("flask_caching").setLevel(logging.ERROR)

    app = Flask(__name__)
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

    # Apply custom config if provided
    if config:
        app.config.update(config)

    if testing:
        app.config["TESTING"] = True

    # Store injected dependencies on app extensions
    # These will be lazily initialized on first request if not provided
    app.extensions["onboard_layout"] = layout
    app.extensions["onboard_bookmark_manager"] = bookmark_manager
    app.extensions["onboard_link_tracker"] = link_tracker

    # Configure caching
    if os.environ.get("FLASK_DEBUG", "False") == "True" or testing:
        cache_config = {"CACHE_TYPE": "flask_caching.backends.nullcache.NullCache"}
    else:
        cache_config = {
            "CACHE_TYPE": "flask_caching.backends.simplecache.SimpleCache",
            "CACHE_DEFAULT_TIMEOUT": 600,
        }
        # Only minify in production
        if not testing:
            try:
                from flask_minify import Minify

                Minify(app=app, html=True, js=True, cssless=True)
            except ImportError:
                pass

    cache = Cache(app, config=cache_config)
    app.extensions["cache"] = cache

    # Set up assets
    assets = Environment(app)
    css = Bundle("css/*.css", filters="cssmin", output="assets/common.css")
    assets.register("css_all", css)
    # Only build in non-testing mode to avoid file I/O issues
    if not testing:
        try:
            css.build()
        except Exception:
            pass

    # Register blueprints
    from app.api.bookmarks import create_bookmarks_blueprint

    app.register_blueprint(create_bookmarks_blueprint())

    # Register main routes
    _register_routes(app, cache)

    # Lazy initialization on first request if dependencies not provided
    @app.before_request
    def ensure_dependencies():
        _ensure_layout(app)
        _ensure_bookmark_manager(app)
        _ensure_link_tracker(app)

    # Production initialization
    if (
        not testing
        and os.environ.get("FLASK_ENV", "development") == "production"
        and not is_test_environment()
    ):
        try:
            logger.info(
                "Production startup: eagerly reloading layout and initializing scheduler"
            )
            _ensure_layout(app)
            app.extensions["onboard_layout"].reload()
            from app.models import apscheduler as apscheduler_module

            apscheduler_module.Scheduler.getScheduler()
        except Exception:
            logger.exception("Failed to eagerly reload layout during production startup")

    return app


def _ensure_layout(app):
    """Ensure layout is initialized."""
    if app.extensions.get("onboard_layout") is None:
        from app.models.layout import Layout

        app.extensions["onboard_layout"] = Layout()


def _ensure_bookmark_manager(app):
    """Ensure bookmark manager is initialized."""
    if app.extensions.get("onboard_bookmark_manager") is None:
        from app.services.bookmark_manager import BookmarkManager

        app.extensions["onboard_bookmark_manager"] = BookmarkManager()


def _ensure_link_tracker(app):
    """Ensure link tracker is initialized."""
    if app.extensions.get("onboard_link_tracker") is None:
        from app.services.link_tracker import LinkTracker

        app.extensions["onboard_link_tracker"] = LinkTracker()


def get_layout(app=None):
    """Get layout from app context or current_app."""
    if app is None:
        from flask import current_app

        app = current_app
    return app.extensions.get("onboard_layout")


def get_bookmark_manager(app=None):
    """Get bookmark manager from app context or current_app."""
    if app is None:
        from flask import current_app

        app = current_app
    return app.extensions.get("onboard_bookmark_manager")


def get_link_tracker(app=None):
    """Get link tracker from app context or current_app."""
    if app is None:
        from flask import current_app

        app = current_app
    return app.extensions.get("onboard_link_tracker")


def _register_routes(app, cache):
    """Register main application routes."""
    from datetime import datetime

    from flask import make_response, redirect, render_template, request

    page_timeout = int(os.environ.get("ONBOARD_PAGE_TIMEOUT", 600))

    @app.context_processor
    def inject_current_date():
        layout = get_layout(app)
        return {
            "today_date": datetime.now(),
            "site_title": os.environ.get("ONBOARD_SITE_TITLE", "OnBoard"),
            "favicon_path": layout.favicon_path if layout else lambda x: None,
        }

    @app.route("/")
    @app.route("/tab/<tab_name>")
    @cache.cached(
        timeout=page_timeout, unless=lambda: get_layout(app).is_modified()
    )
    def index(tab_name=None):
        layout = get_layout(app)
        if layout.is_modified():
            layout.reload()

        if request.headers.get("HX-Request"):
            return render_template("tab_content.html", layout=layout, tab_name=tab_name)
        else:
            return render_template(
                "index.html", layout=layout, tab_name=tab_name, skip_htmx=False
            )

    @app.route("/feed/<feed_id>")
    def feed(feed_id):
        layout = get_layout(app)
        feed = layout.get_feed(feed_id)
        html = render_template(feed.template, widget=feed, skip_htmx=True)
        try:
            from html.parser import HTMLParser

            class HXStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.parts = []

                def _filter_attrs(self, attrs):
                    filtered = []
                    for name, value in attrs:
                        if name in ("hx-trigger", "data-hx-trigger") and value:
                            if "load" in value.split():
                                continue
                        filtered.append((name, value))
                    return filtered

                def handle_starttag(self, tag, attrs):
                    attrs_filtered = self._filter_attrs(attrs)
                    attr_str = "".join(
                        f' {n}="{v}"' if v is not None else f" {n}"
                        for n, v in attrs_filtered
                    )
                    self.parts.append(f"<{tag}{attr_str}>")

                def handle_startendtag(self, tag, attrs):
                    attrs_filtered = self._filter_attrs(attrs)
                    attr_str = "".join(
                        f' {n}="{v}"' if v is not None else f" {n}"
                        for n, v in attrs_filtered
                    )
                    self.parts.append(f"<{tag}{attr_str}/>")

                def handle_endtag(self, tag):
                    self.parts.append(f"</{tag}>")

                def handle_data(self, data):
                    self.parts.append(data)

                def handle_comment(self, data):
                    self.parts.append(f"<!--{data}-->")

                def handle_entityref(self, name):
                    self.parts.append(f"&{name};")

                def handle_charref(self, name):
                    self.parts.append(f"&#{name};")

            stripper = HXStripper()
            stripper.feed(html)
            html = "".join(stripper.parts)
        except Exception:
            pass
        return html

    @app.route("/click_events")
    def click_events():
        link_tracker = get_link_tracker(app)
        df = link_tracker.get_click_events()
        html = df.to_html(classes="data", index=False)
        response = make_response(html)
        response.headers["Content-Type"] = "text/html"
        return response

    @app.route("/redirect/<feed_id>/<link_id>")
    def track(feed_id, link_id):
        layout = get_layout(app)
        link_tracker = get_link_tracker(app)
        link = layout.get_link(feed_id, link_id)
        link_tracker.track_click_event(feed_id, link_id, link)

        if not link:
            logger.warning(
                f"No target link found for feed={feed_id} link={link_id}; redirecting to index"
            )
            return redirect("/", code=302)

        logger.info(f"redirecting to {link}")
        return redirect(str(link), code=302)

    @app.route("/feed/<feed_id>/refresh")
    def refresh(feed_id):
        layout = get_layout(app)
        layout.refresh_feeds(feed_id)
        return redirect("/", code=302)

    @app.route("/bookmarks/manage")
    def bookmarks_manage():
        return render_template("bookmarks_manager.html")

    @app.route("/api/healthcheck")
    def healthcheck():
        return "OK", 200
