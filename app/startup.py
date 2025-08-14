"""Deprecated startup helper.

Startup responsibilities (cache dir computation, archive-on-load, scheduler
registration) were migrated to `FeedCache` and application wiring. This module
is intentionally a no-op to avoid import-time side-effects during tests.
"""

__all__ = []
