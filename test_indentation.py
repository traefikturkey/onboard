#!/usr/bin/env python3
"""
Test file to verify VS Code indentation settings.
This file should maintain 4-space indentation when saved.
"""

def test_function():
    """Test function with nested code to check indentation."""
    if True:
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
            "credentials": {
                "username": "admin",
                "password": "secret"
            }
        },
        "cache": {
            "type": "redis",
            "ttl": 3600
        }
    }
    
    return config


class TestClass:
    """Test class to verify class indentation."""
    
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        """Add an item to the data list."""
        if item not in self.data:
            self.data.append(item)
            return True
        return False
    
    def process_data(self):
        """Process the data with complex nested logic."""
        result = []
        for item in self.data:
            if isinstance(item, str):
                processed = {
                    "original": item,
                    "length": len(item),
                    "uppercase": item.upper()
                }
                result.append(processed)
        return result


if __name__ == "__main__":
    # Test the indentation settings
    test_function()
    
    obj = TestClass()
    obj.add_item("test")
    obj.add_item("hello")
    print(obj.process_data())
