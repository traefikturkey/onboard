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
 
 
##########################################################

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
