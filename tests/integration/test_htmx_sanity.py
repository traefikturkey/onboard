import time


def test_homepage_loads_and_has_htmx(app_process, chrome_driver, app_url):
    url = f"{app_url}/"
    chrome_driver.get(url)
    time.sleep(0.5)
    body = chrome_driver.page_source
    assert "htmx.org" in body or "htmx.min.js" in body
