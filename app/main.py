import asyncio
import logging
import os
import secrets
import signal
import sys
import warnings
from datetime import datetime
from typing import Any

from flask import Flask, make_response, redirect, render_template, request
from flask_assets import Bundle, Environment
from flask_caching import Cache

from app.models import layout as layout_module
from app.services.link_tracker import link_tracker
from app.utils import copy_default_to_configs
from app.models import apscheduler as apscheduler_module

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.WARN)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Silence Flask-Caching informational UserWarning when CACHE_TYPE is 'null'
# and reduce logging noise from the flask_caching logger.
warnings.filterwarnings(
    "ignore",
    message=r"Flask-Caching: CACHE_TYPE is set to null.*",
    category=UserWarning,
)
logging.getLogger("flask_caching").setLevel(logging.ERROR)

copy_default_to_configs()
layout = layout_module.Layout()

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex())


if os.environ.get("FLASK_DEBUG", "False") == "True":
    # Use explicit backend class path to avoid Flask-Caching deprecation warnings
    cache_config = {"CACHE_TYPE": "flask_caching.backends.nullcache.NullCache"}
else:
    # 600 seconds = 10 minutes
    # Use explicit backend class path to avoid Flask-Caching deprecation warnings
    cache_config = {
        "CACHE_TYPE": "flask_caching.backends.simplecache.SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 600,
    }
    from flask_minify import Minify

    Minify(app=app, html=True, js=True, cssless=True)

cache = Cache(app, config=cache_config)
page_timeout = int(os.environ.get("ONBOARD_PAGE_TIMEOUT", 600))

assets = Environment(app)

css = Bundle("css/*.css", filters="cssmin", output="assets/common.css")
assets.register("css_all", css)
css.build()


# Eagerly load layout and initialize scheduler when running in production.
# Tests and other CI runs should skip this; use the same detection logic as
# the Scheduler helper to avoid starting background jobs during tests.
def _is_test_environment() -> bool:
    # Mirror checks used by Scheduler.getScheduler() to detect test runs
    return (
        os.environ.get("ONBOARD_DISABLE_SCHEDULER", "False").lower() == "true"
        or "pytest" in sys.modules
        or "PYTEST_CURRENT_TEST" in os.environ
        or any("test" in arg for arg in sys.argv)
        or "behave" in sys.modules
    )


if os.environ.get("FLASK_ENV", "development") == "production" and not _is_test_environment():
    try:
        logger.info("Production startup: eagerly reloading layout and initializing scheduler")
        # Ensure the layout is loaded before serving requests
        layout.reload()
        # Trigger scheduler initialization (it will respect test flags internally)
        apscheduler_module.Scheduler.getScheduler()
    except Exception:
        logger.exception("Failed to eagerly reload layout during production startup")


@app.context_processor
def inject_current_date():
    return {
        "today_date": datetime.now(),
        "site_title": os.environ.get("ONBOARD_SITE_TITLE", "OnBoard"),
        "favicon_path": layout.favicon_path,
    }


@app.route("/")
@app.route("/tab/<tab_name>")
@cache.cached(timeout=page_timeout, unless=lambda: layout.is_modified)
def index(tab_name=None):
    # Load feeds and bookmarks
    if layout.is_modified():
        layout.reload()

    if request.headers.get("HX-Request"):
        # Return partial content for HTMX requests
        return render_template("tab_content.html", layout=layout, tab_name=tab_name)
    else:
        # Return full page for direct navigation
        return render_template(
            "index.html", layout=layout, tab_name=tab_name, skip_htmx=False
        )


@app.route("/feed/<feed_id>")
def feed(feed_id):
    feed = layout.get_feed(feed_id)
    # logger.debug(f"{feed.name} - {feed.display_items[0].title}")
    return render_template(feed.template, widget=feed, skip_htmx=True)


@app.route("/click_events")
def click_events():
    df = link_tracker.get_click_events()
    html = df.to_html(classes="data", index=False)
    response = make_response(html)
    response.headers["Content-Type"] = "text/html"
    return response


@app.route("/redirect/<feed_id>/<link_id>")
def track(feed_id, link_id):
    link = layout.get_link(feed_id, link_id)
    # defensive: ensure link is a string and handle missing links gracefully
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
    # layout exposes refresh_feeds (plural); call the correct method
    layout.refresh_feeds(feed_id)
    return redirect("/", code=302)


@app.route("/api/healthcheck")
def healthcheck():
    return "OK", 200


###############################################################################
#
# Main Startup Code
#
###############################################################################


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", os.environ.get("ONBOARD_PORT", 9830)))
    development = bool(os.environ.get("FLASK_ENV", "development") == "development")
    if development:
        app.run(port=port, debug=bool(os.environ.get("FLASK_DEBUG", "True")))
        if bool(os.environ.get("WERKZEUG_RUN_MAIN")):
            print("")
            layout.stop_scheduler()
            app.logger.info("Shutting down...")

        sys.exit()
    else:
        try:
            from hypercorn.asyncio import serve
            from hypercorn.config import Config

            shutdown_event = asyncio.Event()

            def _signal_handler(*_: Any) -> None:
                logger.info("Shutting down...")
                layout.stop_scheduler()
                shutdown_event.set()

            config = Config()
            config.accesslog = "-"
            config.errorlog = "-"
            config.loglevel = "DEBUG"
            config.bind = f"0.0.0.0:{port}"
            loop = asyncio.new_event_loop()
            loop.add_signal_handler(signal.SIGTERM, _signal_handler)

            async def _shutdown_trigger() -> None:
                # wait until the event is set, then return None (type-friendly)
                await shutdown_event.wait()
                return None

            loop.run_until_complete(
                serve(app, config, shutdown_trigger=_shutdown_trigger)
            )
        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            layout.stop_scheduler()
            sys.exit()
