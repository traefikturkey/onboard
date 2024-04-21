import asyncio
import logging
import os
import secrets
import signal
import sys
from datetime import datetime
from flask import Flask, make_response, redirect, render_template
from flask_assets import Environment, Bundle
from flask_caching import Cache
from typing import Any
from services.link_tracker import link_tracker
from utils import copy_default_to_configs

logger = logging.getLogger(__name__)

copy_default_to_configs()

from models.layout import layout

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex())


if os.environ.get("FLASK_DEBUG", "False") == "True":
	cache_config={
		'CACHE_TYPE': 'null'
	}
else:
	# 600 seconds = 10 minutes
	cache_config={
		'CACHE_TYPE': 'simple',            
		'CACHE_DEFAULT_TIMEOUT': 600
	}
	from flask_minify import Minify
	Minify(app=app, html=True, js=True, cssless=True)
	
cache = Cache(app, config=cache_config)
page_timeout = int(os.environ.get('ONBOARD_PAGE_TIMEOUT', 600))

assets = Environment(app)

css = Bundle(
		'css/*.css',
		filters="cssmin",
		output="assets/common.css"
)
assets.register('css_all', css)
css.build()

@app.context_processor
def inject_current_date():
	return {
		'today_date': datetime.now(),
		'site_title':	os.environ.get('ONBOARD_SITE_TITLE', 'OnBoard'),
	}



@app.route('/')
@app.route('/tab/<tab_name>')
@cache.cached(timeout=page_timeout, unless=lambda: layout.is_modified)
def index(tab_name=None):
	# Load feeds and bookmarks
	if layout.is_modified():
		layout.reload()	

	return render_template('index.html', layout=layout, tab_name=tab_name, skip_htmx=False)



@app.route('/feed/<feed_id>')
def feed(feed_id):
	feed = layout.get_feed(feed_id)
	return render_template(feed.template, widget=feed, skip_htmx=True)


@app.route('/click_events')
def click_events():
	df = link_tracker.get_click_events()
	html = df.to_html(classes='data', index=False)
	response = make_response(html)
	response.headers["Content-Type"] = "text/html"
	return response

@app.route('/redirect/<feed_id>/<link_id>')
def track(feed_id, link_id):
	link = layout.get_link(feed_id, link_id)
 
	link_tracker.track_click_event(feed_id, link_id, link)
 
	logger.info(f"redirecting to {link}")
	return redirect(link, code=302)


###############################################################################
#
# Main Startup Code
#
###############################################################################

if __name__ == '__main__':	
	port = int(os.environ.get("FLASK_PORT", os.environ.get("ONBOARD_PORT", 9830)))
	development = bool(os.environ.get("FLASK_ENV", "development")  == "development")
	if development:
		app.run(port=port, debug=bool(os.environ.get("FLASK_DEBUG", "True")))
		print ("Shutting down...")
		layout.stop_scheduler()
		sys.exit()
	else:
		try:
			from hypercorn.config import Config
			from hypercorn.asyncio import serve

			shutdown_event = asyncio.Event()

			def _signal_handler(*_: Any) -> None:
				print ("Shutting down...")
				layout.stop_scheduler()
				shutdown_event.set()

			config = Config()
			config.accesslog="-"
			config.errorlog="-"
			config.loglevel="DEBUG"
			config.bind = f"0.0.0.0:{port}"
			loop = asyncio.new_event_loop()
			loop.add_signal_handler(signal.SIGTERM, _signal_handler)
			loop.run_until_complete(
					serve(app, config, shutdown_trigger=shutdown_event.wait)
			)
		except KeyboardInterrupt:
			print ("\nShutting down...")
			layout.stop_scheduler()
			sys.exit()
	