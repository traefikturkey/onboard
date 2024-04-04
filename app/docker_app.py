
from docker import APIClient
from flask import Blueprint

docker_client = APIClient(base_url='unix://var/run/docker.sock')

docker_app = Blueprint('docker_app', __name__, template_folder='templates')

def event_stream():
	events = docker_client.events()
	for event in events:
		yield 'data: {}\n\n'.format(event)

@docker_app.route('/events')
def events():
	return docker_app.response_class(
		event_stream(),
		mimetype='text/event-stream'
)