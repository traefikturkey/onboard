import os
import shutil
import subprocess
import time
import urllib.request

import pytest

SELENIUM_DEFAULT_IMAGE = os.environ.get(
    "SELENIUM_IMAGE", "selenium/standalone-chrome:115.0"
)
SELENIUM_CONTAINER_NAME = os.environ.get(
    "SELENIUM_CONTAINER_NAME", "onboard_test_selenium"
)
SELENIUM_PORT = int(os.environ.get("SELENIUM_PORT", "4444"))
SELENIUM_URL = f"http://127.0.0.1:{SELENIUM_PORT}/wd/hub"


def docker_inspect_ip(name: str) -> str | None:
    """Return the first container network IP for `name`, or None."""
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
    )
    ip = r.stdout.strip()
    return ip or None


@pytest.fixture(scope="session", autouse=True)
def selenium_service():
    """Ensure a selenium standalone container is running for integration tests.

    Starts a container named SELENIUM_CONTAINER_NAME if not present, publishes SELENIUM_PORT
    and waits until the remote WebDriver is responsive. On teardown the container is stopped
    unless SELENIUM_LEAVE_RUNNING=1 is set.
    """
    if shutil.which("docker") is None:
        pytest.skip("docker CLI not available; skipping selenium integration setup")

    def docker_run(cmd):
        return subprocess.run(["docker"] + cmd, capture_output=True, text=True)

    def docker_inspect_ip(name: str) -> str | None:
        r = docker_run(
            [
                "inspect",
                "-f",
                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                name,
            ]
        )
        ip = r.stdout.strip()
        return ip or None

    created = False
    # Prefer any existing container that publishes port 4444
    ps_ports = docker_run(["ps", "--format", "{{.Names}} {{.Ports}}"])
    reuse_name = None
    for line in ps_ports.stdout.splitlines():
        if f"0.0.0.0:{SELENIUM_PORT}->" in line or f":::{SELENIUM_PORT}->" in line:
            reuse_name = line.split()[0]
            break

    selected_container = None
    if reuse_name:
        # ensure it's running and prefer its container-network IP
        docker_run(["start", reuse_name])
        selected_container = reuse_name
    else:
        # check for running container by name
        res = docker_run(
            [
                "ps",
                "--filter",
                f"name={SELENIUM_CONTAINER_NAME}",
                "--format",
                "{{.Names}}",
            ]
        )
        # if not present, we'll either start an existing stopped container or run one
        if SELENIUM_CONTAINER_NAME not in res.stdout.strip().splitlines():
            # check if exists but stopped
            res_all = docker_run(
                [
                    "ps",
                    "-a",
                    "--filter",
                    f"name={SELENIUM_CONTAINER_NAME}",
                    "--format",
                    "{{.Names}}",
                ]
            )
            if SELENIUM_CONTAINER_NAME in res_all.stdout.strip().splitlines():
                docker_run(["start", SELENIUM_CONTAINER_NAME])
                selected_container = SELENIUM_CONTAINER_NAME
            else:
                run_cmd = [
                    "run",
                    "-d",
                    "--name",
                    SELENIUM_CONTAINER_NAME,
                    "-p",
                    f"{SELENIUM_PORT}:{SELENIUM_PORT}",
                    "--shm-size",
                    "2g",
                    SELENIUM_DEFAULT_IMAGE,
                ]
                r = docker_run(run_cmd)
                if r.returncode != 0:
                    pytest.skip(
                        f"Unable to start selenium container: {r.stderr.strip()}"
                    )
                created = True
                selected_container = SELENIUM_CONTAINER_NAME

    # compute runtime URL from container IP when possible, else fall back to localhost
    runtime_url = None
    if selected_container:
        ip = docker_inspect_ip(selected_container)
        if ip:
            runtime_url = f"http://{ip}:{SELENIUM_PORT}/wd/hub"
    if not runtime_url:
        runtime_url = f"http://127.0.0.1:{SELENIUM_PORT}/wd/hub"

    # wait for selenium to be ready (target runtime_url)
    deadline = time.time() + 60
    status_url = runtime_url + "/status"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(status_url, timeout=3) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.5)
    else:
        if created:
            docker_run(["logs", SELENIUM_CONTAINER_NAME])
        pytest.skip(f"Selenium at {status_url} did not become ready in time")

    # export env var for tests that read it at runtime
    os.environ.setdefault("SELENIUM_URL", runtime_url)

    yield runtime_url

    # teardown
    if os.environ.get("SELENIUM_LEAVE_RUNNING") == "1":
        return
    if created:
        docker_run(["stop", SELENIUM_CONTAINER_NAME])
        docker_run(["rm", SELENIUM_CONTAINER_NAME])


@pytest.fixture(scope="session")
def selenium_url(selenium_service):
    """Return the selenium url (ensures selenium_service is started)."""
    return selenium_service


APP_PORT = int(os.environ.get("APP_PORT", "9830"))
APP_URL = os.environ.get("APP_URL", f"http://127.0.0.1:{APP_PORT}")
APP_CONTAINER_NAME = os.environ.get("APP_CONTAINER_NAME", "onboard_test")
APP_IMAGE = os.environ.get("APP_IMAGE", "onboard:prod")


@pytest.fixture(scope="session")
def app_url():
    """Ensure the app production image/container is available and return a reachable URL.

    Builds the image `APP_IMAGE` from the repository `Dockerfile` production stage if missing,
    then starts (or reuses) a container named `APP_CONTAINER_NAME` publishing `APP_PORT`.
    """
    if shutil.which("docker") is None:
        pytest.skip("docker CLI not available; skipping app integration setup")

    def docker_run(cmd):
        return subprocess.run(["docker"] + cmd, capture_output=True, text=True)

    # Always (re)build the production image before starting containers so tests run
    # against a fresh build while still allowing Docker's build cache to speed the process.
    build_cmd = ["build", "--target", "production", "-t", APP_IMAGE, "."]
    r = docker_run(build_cmd)
    if r.returncode != 0:
        pytest.skip(f"App image {APP_IMAGE} build failed: {r.stderr.strip()}")

    created = False
    # prefer any container that already publishes the app port
    ps_ports = docker_run(["ps", "--format", "{{.Names}} {{.Ports}}"])
    reuse_name = None
    for line in ps_ports.stdout.splitlines():
        if f"0.0.0.0:{APP_PORT}->" in line or f":::{APP_PORT}->" in line:
            reuse_name = line.split()[0]
            break

    if reuse_name:
        docker_run(["start", reuse_name])
        selected_app = reuse_name
    else:
        # check for container by name
        res = docker_run(
            ["ps", "--filter", f"name={APP_CONTAINER_NAME}", "--format", "{{.Names}}"]
        )
        if APP_CONTAINER_NAME not in res.stdout.strip().splitlines():
            res_all = docker_run(
                [
                    "ps",
                    "-a",
                    "--filter",
                    f"name={APP_CONTAINER_NAME}",
                    "--format",
                    "{{.Names}}",
                ]
            )
            if APP_CONTAINER_NAME in res_all.stdout.strip().splitlines():
                docker_run(["start", APP_CONTAINER_NAME])
            else:
                # Remove any running container publishing APP_PORT to avoid
                # 'port is already allocated' when creating the fresh test container.
                ps_ports_conflicts = docker_run(
                    ["ps", "--format", "{{.Names}} {{.Ports}}"]
                )
                for line in ps_ports_conflicts.stdout.splitlines():
                    if f"0.0.0.0:{APP_PORT}->" in line or f":::{APP_PORT}->" in line:
                        conflict_name = line.split()[0]
                        if conflict_name != APP_CONTAINER_NAME:
                            docker_run(["rm", "-f", conflict_name])

                r = docker_run(
                    [
                        "run",
                        "-d",
                        "--name",
                        APP_CONTAINER_NAME,
                        "-p",
                        f"{APP_PORT}:{APP_PORT}",
                        APP_IMAGE,
                    ]
                )
                if r.returncode != 0:
                    pytest.skip(f"Unable to start app container: {r.stderr.strip()}")
                created = True
                selected_app = APP_CONTAINER_NAME
    # compute app runtime URL (use container network IP when possible)
    computed_app_url = None
    if 'selected_app' in locals():
        ip = docker_inspect_ip(selected_app)
        if ip:
            computed_app_url = f"http://{ip}:{APP_PORT}"

    if not computed_app_url:
        computed_app_url = APP_URL

    # wait for app to be ready at computed_app_url
    deadline = time.time() + 60
    status_url = computed_app_url + "/"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(status_url, timeout=3) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.5)
    else:
        if created:
            docker_run(["logs", APP_CONTAINER_NAME])
        pytest.skip(f"App at {status_url} did not become ready in time")

    os.environ.setdefault("APP_URL", computed_app_url)

    yield computed_app_url

    if os.environ.get("APP_LEAVE_RUNNING") == "1":
        return
    if created:
        docker_run(["stop", APP_CONTAINER_NAME])
        docker_run(["rm", APP_CONTAINER_NAME])
