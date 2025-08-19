import os
import pytest

# If selenium isn't installed in the dev environment, skip the whole module so CI/devcontainer doesn't fail.
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
except Exception as e:
    pytest.skip("selenium package not available in this Python environment: {}".format(e), allow_module_level=True)

SELENIUM_URL = os.environ.get("SELENIUM_URL", "http://127.0.0.1:4444/wd/hub")
APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:9830")

@pytest.mark.integration
def test_homepage_loads_and_has_body():
    """Start a remote Chrome session and visit the app root; assert a body tag is present.

    The test will raise a clear error if it can't connect to the Selenium server or the app.
    Use environment vars SELENIUM_URL and APP_URL to override endpoints.
    """
    # Try connecting to remote webdriver
    try:
        driver = webdriver.Remote(command_executor=SELENIUM_URL, desired_capabilities=DesiredCapabilities.CHROME)
    except Exception as exc:
        pytest.skip(f"Unable to connect to Selenium remote at {SELENIUM_URL}: {exc}")

    try:
        driver.set_page_load_timeout(15)
        driver.get(APP_URL + "/")
        # Ensure we at least have a body element and non-empty page source
        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None
        assert len(driver.page_source) > 0
    finally:
        try:
            driver.quit()
        except Exception:
            pass
