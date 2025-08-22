import pytest


@pytest.mark.integration
def test_onboard_prod_container_network_ip(app_url):
    """Verify the `app_url` fixture returns a container-network URL (not localhost).

    Prints the fixture-provided URL and asserts the host portion doesn't start
    with 127.0.0.
    """
    assert app_url, "app_url fixture returned empty"
    host = app_url.split("//", 1)[-1].split(":", 1)[0]
    assert not host.startswith(
        "127.0.0."
    ), f"Container IP unexpectedly localhost: {host}"
