import os
import subprocess
import time
import urllib.request

import pytest

# Configuration
SELENIUM_IMAGE = "selenium/standalone-chrome"
SELENIUM_CONTAINER_NAME = "onboard_test_selenium"
SELENIUM_PORT = "4444"

APP_PORT = "9830"
APP_CONTAINER_NAME = "onboard_test"
APP_IMAGE = "onboard:prod"

# Global variables to store URLs
_SELENIUM_URL = None
_APP_URL = None


def pytest_sessionstart(session):
    """Called after the Session object has been created and configured."""
    global _SELENIUM_URL, _APP_URL

    # Setup containers here - this runs BEFORE any test names are printed
    _SELENIUM_URL = _setup_selenium()
    _APP_URL = _setup_app()

    if _SELENIUM_URL:
        print(f"[tests] Selenium URL: {_SELENIUM_URL}")
        os.environ["SELENIUM_URL"] = _SELENIUM_URL

    if _APP_URL:
        print(f"[tests] App URL: {_APP_URL}")
        os.environ["APP_URL"] = _APP_URL


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    docker_run(["rm", "-f", APP_CONTAINER_NAME])


def _setup_selenium():
    """Setup selenium container and return URL. Reuse if already running and healthy."""
    # Check if selenium container is already running
    result = docker_run(
        ["ps", "--filter", f"name={SELENIUM_CONTAINER_NAME}", "--format", "{{.Names}}"]
    )

    if SELENIUM_CONTAINER_NAME in result.stdout:
        # Container exists and is running, check if it's healthy
        ip = docker_inspect_ip(SELENIUM_CONTAINER_NAME)
        if ip:
            selenium_url = f"http://{ip}:{SELENIUM_PORT}/wd/hub"
            if wait_for_service(f"{selenium_url}/status", timeout=10):
                return selenium_url
            else:
                print(
                    f"[tests] Existing selenium container unhealthy, removing and recreating"
                )
                docker_run(["rm", "-f", SELENIUM_CONTAINER_NAME])
        else:
            print(
                f"[tests] Cannot get IP for existing selenium container, removing and recreating"
            )
            docker_run(["rm", "-f", SELENIUM_CONTAINER_NAME])

    # Start new selenium container
    print(f"[tests] Starting new selenium container: {SELENIUM_CONTAINER_NAME}")
    run_cmd = [
        "run",
        "-d",
        "--name",
        SELENIUM_CONTAINER_NAME,
        "-p",
        f"{SELENIUM_PORT}:{SELENIUM_PORT}",
        "--shm-size",
        "2g",
        SELENIUM_IMAGE,
    ]
    result = docker_run(run_cmd)
    if result.returncode != 0:
        print(f"[tests] Failed to start selenium container: {result.stderr}")
        return None

    # Get container IP
    ip = docker_inspect_ip(SELENIUM_CONTAINER_NAME)
    if not ip:
        print(
            f"[tests] Could not get IP for selenium container {SELENIUM_CONTAINER_NAME}"
        )
        return None

    selenium_url = f"http://{ip}:{SELENIUM_PORT}/wd/hub"

    # Wait for selenium to be ready
    if not wait_for_service(f"{selenium_url}/status"):
        print(f"[tests] Selenium at {selenium_url} did not become ready in time")
        return None

    return selenium_url


def _setup_app():
    """Setup app container and return URL."""
    # Stop and cleanup any running onboard production containers (exclude devcontainers and selenium)
    result = docker_run(["ps", "-a", "--format", "{{.Names}} {{.Image}}"])
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            name, image = parts[0], parts[1]
            # Only clean up production onboard containers, never devcontainers or selenium
            # Skip if: name starts with vsc-, image starts with vsc-, name ends with _devcontainer, or is selenium
            if (
                not name.startswith("vsc-")
                and not image.startswith("vsc-")
                and not name.endswith("_devcontainer")
                and name != SELENIUM_CONTAINER_NAME
                and ("onboard" in name.lower() or "onboard" in image.lower())
            ):
                print(f"[tests] Stopping and removing container: {name}")
                docker_run(["rm", "-f", name])

    # Build production image
    print(f"[tests] Building production image: {APP_IMAGE}")
    build_result = docker_run(["build", "--target", "production", "-t", APP_IMAGE, "."])
    if build_result.returncode != 0:
        print(f"[tests] Failed to build app image: {build_result.stderr}")
        return None

    # Start new production container
    run_cmd = [
        "run",
        "-d",
        "--name",
        APP_CONTAINER_NAME,
        "-p",
        f"{APP_PORT}:{APP_PORT}",
        APP_IMAGE,
    ]
    result = docker_run(run_cmd)
    if result.returncode != 0:
        print(f"[tests] Failed to start app container: {result.stderr}")
        return None

    # Get container IP
    ip = docker_inspect_ip(APP_CONTAINER_NAME)
    if not ip:
        print(f"[tests] Could not get IP for app container {APP_CONTAINER_NAME}")
        return None

    app_url = f"http://{ip}:{APP_PORT}"

    # Wait for app to be ready
    if not wait_for_service(app_url):
        # Print logs for debugging
        logs = docker_run(["logs", APP_CONTAINER_NAME])
        print(f"[tests] App container logs:\n{logs.stdout}")
        print(f"[tests] App at {app_url} did not become ready in time")
        return None

    return app_url


def docker_inspect_ip(name: str) -> str | None:
    """Return the first container network IP for `name`, or None."""
    try:
        r = subprocess.run(
            [
                "docker",
                "inspect",
                "-f",
                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        ip = r.stdout.strip()
        return ip or None
    except Exception:
        return None


def docker_run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a docker command and return the result."""
    return subprocess.run(["docker"] + cmd, capture_output=True, text=True)


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """Wait for a service to become available at the given URL."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def selenium_url():
    """Return the pre-setup selenium URL."""
    return _SELENIUM_URL


@pytest.fixture(scope="session")
def app_url():
    """Return the pre-setup app URL."""
    return _APP_URL
