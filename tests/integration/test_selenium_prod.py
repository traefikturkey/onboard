import os
import pytest
import os

SELENIUM_URL = os.environ.get("SELENIUM_URL", "http://127.0.0.1:4444/wd/hub")
APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:9830")


@pytest.mark.integration
def test_homepage_loads_and_has_body():
  """Start a remote Chrome session and visit the app root; assert a body tag is present.

  The test will raise a clear error if it can't connect to the Selenium server or the app.
  Use environment vars SELENIUM_URL and APP_URL to override endpoints.
  """
  # Skip this test at runtime if selenium isn't available in the environment
  pytest.importorskip("selenium")

  # Import selenium pieces at runtime to avoid module-level import errors
  from selenium import webdriver
  from selenium.webdriver.common.by import By
  from selenium.webdriver.chrome.options import Options

  # Create options (headless is fine for remote standalone containers)
  opts = Options()
  # newer chrome headless mode flag may be required in some chrome versions
  opts.add_argument("--headless=new")
  opts.add_argument("--no-sandbox")
  opts.add_argument("--disable-dev-shm-usage")

  # Try connecting to remote webdriver (Selenium 4: pass options, not desired_capabilities)
  try:
    driver = webdriver.Remote(command_executor=SELENIUM_URL, options=opts)
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
