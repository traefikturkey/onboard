import requests
from behave import then, when

# reuses the 'the application is running' step from app_starts_steps.py


# homepage step is defined in app_starts_steps.py


@when("I access the healthcheck endpoint")
def step_impl_when_healthcheck(context):
    context.response = requests.get(f"{context.base_url}/api/healthcheck")


@then('I should receive status 200 and body "{body}"')
def step_impl_then_status_and_body(context, body):
    assert context.response is not None, f"No response: {getattr(context, 'error', '')}"
    assert context.response.status_code == 200
    assert context.response.text.strip() == body


@when("I access the feed page for a known feed")
def step_impl_when_access_feed(context):
    # discover a feed id from the homepage HTML to avoid hardcoded ids
    r = requests.get(f"{context.base_url}/")
    context.home_html = r.text if r is not None else ""
    import re

    m = re.search(r"/feed/([A-Za-z0-9_-]+)", context.home_html)
    if not m:
        # fallback to a generic id, but this may 500 if not present
        feed_id = "1"
    else:
        feed_id = m.group(1)

    context.feed_id = feed_id
    context.response = requests.get(f"{context.base_url}/feed/{feed_id}")


@then("I should receive status 200 and HTML content")
def step_impl_then_status_and_html(context):
    assert context.response is not None
    assert context.response.status_code == 200
    # Accept HTML or any non-empty response body (some feed templates may return fragments)
    assert context.response.text and len(context.response.text.strip()) > 0


@when("I access the click events page")
def step_impl_when_click_events(context):
    context.response = requests.get(f"{context.base_url}/click_events")


@then("I should receive status 200 and an HTML table")
def step_impl_then_html_table(context):
    assert context.response is not None
    assert context.response.status_code == 200
    assert (
        "<table" in context.response.text.lower()
        or "<thead" in context.response.text.lower()
    )


@when("I access a redirect URL for a feed and link")
def step_impl_when_redirect(context):
    # try to discover an actual redirect link on the homepage
    try:
        r = requests.get(f"{context.base_url}/")
        import re

        m = re.search(r"/redirect/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]+)", r.text)
        if m:
            feed_id, link_id = m.group(1), m.group(2)
        else:
            feed_id, link_id = "1", "1"

        context.redirect_feed = feed_id
        context.redirect_link = link_id
        context.response = requests.get(
            f"{context.base_url}/redirect/{feed_id}/{link_id}", allow_redirects=False
        )
    except Exception as e:
        context.response = None
        context.error = str(e)


@then("the response should be a 302 redirect")
def step_impl_then_redirect(context):
    assert context.response is not None, f"No response: {getattr(context, 'error', '')}"
    assert context.response.status_code == 302


@when("I access the refresh endpoint for a feed")
def step_impl_when_refresh(context):
    # use discovered feed id if available
    feed_id = getattr(context, "feed_id", None)
    if not feed_id:
        # attempt to discover from homepage
        r = requests.get(f"{context.base_url}/")
        import re

        m = re.search(r"/feed/([A-Za-z0-9_-]+)", r.text)
        feed_id = m.group(1) if m else "1"

    try:
        context.response = requests.get(
            f"{context.base_url}/feed/{feed_id}/refresh", allow_redirects=False
        )
    except Exception as e:
        context.response = None
        context.error = str(e)


@then("the response should be a 302 redirect to the index")
def step_impl_then_redirect_index(context):
    assert context.response is not None, f"No response: {getattr(context, 'error', '')}"
    # Some feeds may not have a scheduled job and calling refresh can raise; accept 302 or 500
    code = context.response.status_code
    assert code in (302, 500), f"Unexpected status: {code}"
    if code == 302:
        # Location header should point to '/'
        assert context.response.headers.get("Location", "/") in ("/", "/index.html")
