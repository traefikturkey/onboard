
#docker_client = APIClient(base_url='unix://var/run/docker.sock')

# def docker_event_stream():
#   events = docker_client.events()
#   for event in events:
#     yield 'data: {}\n\n'.format(event)

# @app.route('/events')
# def events():
#   return app.response_class(
#     docker_event_stream(),
#     mimetype='text/event-stream'
# )