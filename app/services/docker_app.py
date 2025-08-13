import json

from docker import DockerClient
from flask import Blueprint, current_app, render_template

docker_client = DockerClient(base_url="unix://var/run/docker.sock")

docker_app = Blueprint("docker_app", __name__, template_folder="templates")


def event_stream():
    events = docker_client.events()
    for event in events:
        yield "data: {}\n\n".format(event)


@docker_app.route("/events")
def events():
    return current_app.response_class(event_stream(), mimetype="text/event-stream")


def docker_event_stream():
    events = docker_client.events(decode=True)
    for event in events:
        yield "data: {}\n\n".format(json.dumps(event))


@docker_app.route("/docker_containers")
def containers():
    containers = docker_client.containers.list(filters={"status": "running"})
    return render_template("docker_containers.html", containers=containers)
