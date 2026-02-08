import pytest

pytestmark = pytest.mark.integration


def test_add_tab_button_visible(page, base_url):
    """Verify '+' tab button is present in the tab bar."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    add_btn = page.locator(".add-tab-btn")
    assert add_btn.count() > 0
    assert add_btn.first.text_content().strip() == "+"


def test_add_tab_creates_and_navigates(page, base_url):
    """Click '+', enter name, verify new tab appears."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Click the add tab button
    page.locator(".add-tab-btn").click()

    # Wait for modal to appear
    page.locator("#addTabModal.active").wait_for(state="visible", timeout=5000)

    # Enter tab name
    page.fill("#newTabName", "Integration Test Tab")

    # Submit
    page.locator("#addTabModal .modal-btn-primary").click()

    # Wait for navigation
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Verify new tab appears in tab bar
    tab_links = page.locator(".tab-bar a:not(.add-tab-btn)")
    tab_names = [tab_links.nth(i).text_content().strip() for i in range(tab_links.count())]
    assert "Integration Test Tab" in tab_names


def test_add_widget_button_visible_in_edit_mode(page, base_url):
    """Enter edit mode, verify 'Add Feed' button becomes visible."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Add Feed button should be hidden initially
    add_widget_btn = page.locator(".add-widget-btn").first
    assert not add_widget_btn.is_visible()

    # Enter edit mode
    page.locator("#edit-mode-toggle").click()
    page.locator("body.edit-mode").wait_for(state="attached", timeout=5000)

    # Now Add Feed button should be visible
    visible_btns = page.locator(".add-widget-btn:visible")
    assert visible_btns.count() > 0


def test_move_widget_menu_shows_tabs(page, base_url):
    """Enter edit mode, click move icon on a widget, verify dropdown shows other tab names."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Enter edit mode
    page.locator("#edit-mode-toggle").click()
    page.locator("body.edit-mode").wait_for(state="attached", timeout=5000)

    # Find a move button
    move_btns = page.locator(".move-btn:visible")
    if move_btns.count() == 0:
        pytest.skip("No move buttons found")

    # Click the first move button
    move_btns.first.click()
    page.wait_for_timeout(500)

    # Verify dropdown appears with tab names
    dropdown = page.locator(".move-dropdown:visible")
    assert dropdown.count() > 0
    dropdown_links = dropdown.first.locator("a")
    assert dropdown_links.count() > 0


def test_move_widget_via_menu(page, base_url):
    """Move a widget via the context menu and verify it disappears from source tab."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Count widgets before
    initial_widgets = page.locator(".widget-wrapper").count()
    if initial_widgets == 0:
        pytest.skip("No widgets found")

    # Enter edit mode
    page.locator("#edit-mode-toggle").click()
    page.locator("body.edit-mode").wait_for(state="attached", timeout=5000)

    # Click first move button
    move_btns = page.locator(".move-btn:visible")
    if move_btns.count() == 0:
        pytest.skip("No move buttons found")

    move_btns.first.click()
    page.wait_for_timeout(500)

    # Click first tab in dropdown
    dropdown_links = page.locator(".move-dropdown:visible a")
    if dropdown_links.count() == 0:
        pytest.skip("No move destinations available")

    dropdown_links.first.click()

    # Wait for page reload
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Widget count should be less
    final_widgets = page.locator(".widget-wrapper").count()
    assert final_widgets < initial_widgets


def test_delete_tab_via_api(page, base_url):
    """Delete a tab via the API and verify it's removed."""
    page.goto(f"{base_url}/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # First, create a tab to delete
    result = page.evaluate("""
        async () => {
            const resp = await fetch('/api/layout/tabs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'ToDelete' })
            });
            return resp.ok;
        }
    """)

    # Reload to see the new tab
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    tab_links = page.locator(".tab-bar a:not(.add-tab-btn)")
    tab_names_before = [tab_links.nth(i).text_content().strip() for i in range(tab_links.count())]

    if "ToDelete" not in tab_names_before:
        pytest.skip("Could not create test tab")

    # Delete via API
    page.evaluate("""
        async () => {
            const resp = await fetch('/api/layout/tabs/ToDelete', { method: 'DELETE' });
            return resp.ok;
        }
    """)

    # Reload and verify
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    tab_links = page.locator(".tab-bar a:not(.add-tab-btn)")
    tab_names_after = [tab_links.nth(i).text_content().strip() for i in range(tab_links.count())]
    assert "ToDelete" not in tab_names_after
