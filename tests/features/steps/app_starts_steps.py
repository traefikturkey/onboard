import requests
from behave import given, then, when


@given("the application is running")
def step_impl_given_running(context):
    # Assume the app is running on localhost:5000
    context.base_url = "http://localhost:5000"


@when("I access the homepage")
def step_impl_when_access_homepage(context):
    try:
        context.response = requests.get(context.base_url)
    except Exception as e:
        context.response = None
        context.error = str(e)


@then("I should see a webpage displayed")
def step_impl_then_see_webpage(context):
    assert (
        context.response is not None
    ), f"No response received: {getattr(context, 'error', '')}"
    assert (
        context.response.status_code == 200
    ), f"Unexpected status code: {getattr(context.response, 'status_code', None)}"
    assert (
        "<html" in context.response.text.lower()
    ), "Response does not contain HTML content"
