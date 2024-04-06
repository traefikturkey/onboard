import json
import os
import asyncio
import signal
from datetime import datetime
import sys
from typing import Any
from flask import Flask, request, render_template
from flask_caching import Cache

from utils import copy_default_to_configs
from rss import rss
from yaml_parser import yaml_parser
import docker



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
feeds = {}

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
@cache.cached(timeout=page_timeout)
async def index(tab_name=None):
	# Load feeds and bookmarks
	layout = yaml_parser.load_layout()
	headers = layout['headers']
	
	tabs = layout['tabs']
	current_tab = tabs[0] if tab_name is None else next((tab for tab in tabs if tab['name'].lower() == tab_name.lower()), tabs[0])
	
	column_count = current_tab.get('columns', 3)
	columns = [[] for _ in range(column_count)]
	
	# Add feeds to the appropriate column
	if current_tab['widgets']:
		for widget in current_tab['widgets']:
			widget['articles'] = []
			widget['summary_enabled'] = widget.get('summary_enabled', True)
			column_index = (widget.get('column', 1) - 1) % column_count
			columns[column_index].append(widget)
			match widget['type']:
				case 'bookmarks':
					widget['article_limit'] = -1
					widget['articles'] = [{'title': entry['title'], 'link': entry['url']} for entry in widget['bookmarks']]
				case 'feed':
					widget['hx-get'] = '/rss/' + widget['name']
					feeds[widget['name']] = widget
				case 'docker_events':
					widget['template'] = 'docker_events.html'
				case 'docker_containers':
					widget['hx-get'] = '/docker_containers'
					widget['template'] = 'docker_containers.html'
				case _:
					pass
	
	# Pass column data to the template
	return render_template('index.html', tabs=tabs, columns=columns, headers=headers, current_tab_name=current_tab['name'])

@app.route('/rss/<widget_name>')
@cache.cached(timeout=page_timeout)
async def widget(widget_name):
	widget = await rss.load_feed(feeds[widget_name])
	return render_template('widget.html', widget=widget)

if __name__ == '__main__':
	port = int(os.environ.get("ONBOARD_PORT", 9830))
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
	