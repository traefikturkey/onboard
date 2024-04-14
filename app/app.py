import asyncio
import docker
import json
import os
import signal
import sys
from datetime import datetime
from typing import Any
from flask import Flask, render_template
from flask_assets import Environment, Bundle
from flask_caching import Cache

from utils import copy_default_to_configs
from rss import rss
from layout import layout

copy_default_to_configs()

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

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
	return {'today_date': datetime.now()}

docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

def docker_event_stream():
	events = docker_client.events(decode=True)
	for event in events:
		yield 'data: {}\n\n'.format(json.dumps(event))

@app.route('/events')
def events():
	return app.response_class(
		docker_event_stream(),
		mimetype='text/event-stream'
	)

@app.route('/docker_containers')
def containers():
	containers = docker_client.containers.list(filters={'status':'running'})
	return render_template('docker_containers.html', containers=containers)

@app.route('/')
@app.route('/tab/<tab_name>')
@cache.cached(timeout=page_timeout, unless=lambda: layout.is_modified)
def index(tab_name=None):
	# Load feeds and bookmarks
	layout.reload()	

	return render_template('index.html', layout=layout, tab_name=tab_name)

@app.route('/rss/<widget_name>')
#@cache.cached(timeout=page_timeout, unless=lambda: layout.is_modified)
def widget(widget_name):
	#widget = await rss.load_feed(layout.feed(widget_name))
	widget = layout.feed(widget_name)
	return render_template('widget.html', widget=widget)

if __name__ == '__main__':	
	port = int(os.environ.get("FLASK_PORT", os.environ.get("ONBOARD_PORT", 9830)))
	development = bool(os.environ.get("FLASK_ENV", "development")  == "development")
	if development:
		app.run(port=port, debug=bool(os.environ.get("FLASK_DEBUG", "True")))
		sys.exit()
	try:
		from hypercorn.config import Config
		from hypercorn.asyncio import serve

		shutdown_event = asyncio.Event()

		def _signal_handler(*_: Any) -> None:
			print ("Shutting down...")
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
		sys.exit()
	