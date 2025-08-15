#!/usr/bin/env python3
"""
Test file to verify VS Code indentation settings.
This file should maintain 4-space indentation when saved.
"""

def test_function():
    """Smoke test to exercise indentation sample without returning a value (avoid PytestReturnNotNoneWarning)."""
    if True:  # intentional simple branch
        print("This should be indented with 4 spaces")
        for i in range(3):
            if i % 2 == 0:
                print(f"Number {i} is even")
            else:
                print(f"Number {i} is odd")

    # Nested dictionary to test complex indentation
    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {"username": "admin", "password": "secret"},
        },
        "cache": {"type": "redis", "ttl": 3600},
    }

    # Minimal assertion instead of returning object
    assert config["database"]["host"] == "localhost"

class IndentationHelper:
    """Helper class (renamed from TestClass to avoid collection warning)."""

    def __init__(self):  # simple container
        self.data = []

    def add_item(self, item):
        if item not in self.data:
            self.data.append(item)
            return True
        return False

    def process_data(self):
        result = []
        for item in self.data:
            if isinstance(item, str):
                result.append(
                    {"original": item, "length": len(item), "uppercase": item.upper()}
                )
        return result


if __name__ == "__main__":
    test_function()
    helper = IndentationHelper()
    helper.add_item("test")
    helper.add_item("hello")
    print(helper.process_data())
