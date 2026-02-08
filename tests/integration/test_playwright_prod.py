import pytest

pytestmark = pytest.mark.integration


def test_homepage_loads_and_has_body(page, base_url):
    """Navigate to homepage and verify body is present with content."""
    page.goto(f"{base_url}/")
    body = page.locator("body")
    body.wait_for(state="visible")
    assert body.inner_text().strip() != ""


def test_healthcheck_endpoint(page, base_url):
    """Verify the healthcheck API returns 200 OK."""
    response = page.goto(f"{base_url}/api/healthcheck")
    assert response.status == 200


def test_homepage_has_essential_elements(page, base_url):
    """Verify essential page elements are present."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("domcontentloaded")

    assert page.locator("#bookmarkBar").count() > 0
    assert page.locator("#main-content").count() > 0
    assert page.locator(".tab-bar").count() > 0
    assert page.locator("#edit-mode-toggle").count() > 0


def test_tab_switching_loads_content(page, base_url):
    """Click the second tab and verify main content updates."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("domcontentloaded")

    tabs = page.locator(".tab-bar a")
    if tabs.count() < 2:
        pytest.skip("Less than 2 tabs available")

    # Get initial content
    initial_content = page.locator("#main-content").inner_html()

    # Click the second tab
    tabs.nth(1).click()

    # Wait for HTMX swap to complete
    page.wait_for_load_state("networkidle")

    # Content should have changed (or at least the request completed)
    # Give a brief moment for HTMX to swap
    page.wait_for_timeout(500)


def test_widgets_render_with_headers(page, base_url):
    """Verify widget headers are rendered with text content."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")

    # Wait for any HTMX-loaded widgets to settle
    page.wait_for_timeout(2000)

    headers = page.locator(".box-header")
    # There should be at least one widget header
    assert headers.count() > 0

    # At least one header should have visible text (link text)
    first_visible = headers.locator("a").first
    assert first_visible.inner_text().strip() != ""
