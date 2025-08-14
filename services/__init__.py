"""Compatibility shim: make `services` a package that points to `app/services`.

This allows legacy imports like `import services.link_tracker` to resolve
without changing existing import statements across the codebase.
"""
import os

# Point this package's search path to the real services directory under app/
this_dir = os.path.dirname(__file__)
services_path = os.path.abspath(os.path.join(this_dir, "..", "app", "services"))
__path__ = [services_path]
