import os
import sys


def is_test_environment() -> bool:
    """Centralized detection for test environments.

    This function consolidates the heuristic used across the app for
    skipping scheduler startup and other test-only behavior.
    """
    return (
        os.environ.get("ONBOARD_DISABLE_SCHEDULER", "False").lower() == "true"
        or "pytest" in sys.modules
        or "PYTEST_CURRENT_TEST" in os.environ
        or any("test" in arg for arg in sys.argv)
        or "behave" in sys.modules
    )
