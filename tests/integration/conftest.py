import time
import subprocess
import os
import signal
import socket

import pytest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="session")
def app_process():
    """Start the Flask app in a subprocess on port 9830 for integration tests."""
    env = os.environ.copy()
    env.setdefault("ONBOARD_PORT", "9830")
    # Start the app with uv run to match project setup
    proc = subprocess.Popen(["uv", "run", "python", "run.py"], env=env)
    # wait for port to open
    timeout = 10
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", 9830), timeout=1):
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.skip("App did not start on port 9830")

    yield proc

    # Teardown
    try:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


@pytest.fixture
def chrome_driver():
    """Provide a headless Chrome WebDriver, skip if not available."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        # Prefer a remote Selenium endpoint if provided (useful with selenium/standalone containers)
        remote_url = os.environ.get("SELENIUM_REMOTE_URL")
        if remote_url:
            driver = webdriver.Remote(command_executor=remote_url, options=options)
        else:
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        pytest.skip(f"Chrome WebDriver not available: {e}")
        return
    yield driver
    try:
        driver.quit()
    except Exception:
        pass


@pytest.fixture
def app_url():
    """URL that the browser should use to reach the running app.

    Use `ONBOARD_TEST_URL` when the browser runs inside a container and cannot
    reach `127.0.0.1` on the host. Default stays localhost for developer runs.
    """
    return os.environ.get("ONBOARD_TEST_URL", "http://127.0.0.1:9830")
