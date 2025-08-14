import runpy
import sys
import types


def test_flask_debug_branch_uses_nullcache(monkeypatch):
    # Prepare a fake flask_caching module to capture the config passed into Cache
    captured = {}

    class FakeCache:
        def __init__(self, app, config=None):
            captured["config"] = config

        def cached(self, *a, **kw):
            def _decor(fn):
                return fn

            return _decor

    fake_mod = types.ModuleType("flask_caching")
    fake_mod.Cache = FakeCache
    # Ensure our fake module is used when the app module imports flask_caching
    monkeypatch.setitem(sys.modules, "flask_caching", fake_mod)

    # Prevent the Flask server from actually running during module execution
    import flask

    def _noop_run(self, *a, **kw):
        return None

    monkeypatch.setattr(flask.Flask, "run", _noop_run, raising=False)

    # Set FLASK_DEBUG to True so the module selects the nullcache backend
    monkeypatch.setenv("FLASK_DEBUG", "True")

    # Stub flask_assets.Bundle and Environment so css.build() is a no-op
    fake_flask_assets = types.ModuleType("flask_assets")

    class FakeBundle:
        def __init__(self, *a, **kw):
            pass

        def build(self):
            return None

    class FakeEnvironment:
        def __init__(self, app):
            pass

        def register(self, name, bundle):
            return None

    fake_flask_assets.Bundle = FakeBundle
    fake_flask_assets.Environment = FakeEnvironment
    sys.modules["flask_assets"] = fake_flask_assets

    # Execute the module as __main__ to run top-level code; it will import our fake
    try:
        # Ensure a clean import to avoid warnings about pre-existing module entries
        sys.modules.pop("app.app", None)
        runpy.run_module("app.app", run_name="__main__")
    except SystemExit:
        # __main__ may call sys.exit(); that's fine
        pass

    assert "config" in captured
    assert "nullcache" in str(captured["config"]["CACHE_TYPE"]).lower()


def test_main_development_calls_stop_scheduler(monkeypatch):
    # Run the module as __main__ with FLASK_ENV=development but stub out app.run
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("FLASK_DEBUG", "False")
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "1")

    import flask

    import app.models.layout as layout_module

    # Stub Flask.run to avoid starting the real server
    def _noop_run(self, *a, **kw):
        return None

    monkeypatch.setattr(flask.Flask, "run", _noop_run, raising=False)

    called = {"stopped": False}

    def fake_stop(self):
        called["stopped"] = True

    # Patch the Layout.stop_scheduler so when the __main__ code calls it we record it
    monkeypatch.setattr(
        layout_module.Layout, "stop_scheduler", fake_stop, raising=False
    )

    # Ensure flask_assets is stubbed here as well
    fake_flask_assets = types.ModuleType("flask_assets")

    class FakeBundle:
        def __init__(self, *a, **kw):
            pass

        def build(self):
            return None

    class FakeEnvironment:
        def __init__(self, app):
            pass

        def register(self, name, bundle):
            return None

    fake_flask_assets.Bundle = FakeBundle
    fake_flask_assets.Environment = FakeEnvironment
    sys.modules["flask_assets"] = fake_flask_assets

    try:
        sys.modules.pop("app.app", None)
        runpy.run_module("app.app", run_name="__main__")
    except SystemExit:
        # expected sys.exit() at the end of the __main__ development branch
        pass

    assert called["stopped"] is True


def test_main_production_hypercorn_shutdown(monkeypatch):
    # Simulate production branch and ensure signal handler triggers stop_scheduler
    monkeypatch.setenv("FLASK_ENV", "production")

    import app.models.layout as layout_module

    called = {"stopped": False, "added_signal": False, "run": False}

    def fake_stop(self):
        called["stopped"] = True

    monkeypatch.setattr(
        layout_module.Layout, "stop_scheduler", fake_stop, raising=False
    )

    # Fake hypercorn.asyncio.serve to a simple sentinel (not awaitable)
    fake_hypercorn_mod = types.ModuleType("hypercorn")
    fake_asyncio = types.ModuleType("hypercorn.asyncio")

    def fake_serve(*a, **kw):
        called["run"] = True
        return "SENTINEL"

    fake_asyncio.serve = fake_serve
    sys.modules["hypercorn"] = fake_hypercorn_mod
    sys.modules["hypercorn.asyncio"] = fake_asyncio

    # Provide a fake Config class expected by the module
    fake_config_mod = types.ModuleType("hypercorn.config")

    class FakeConfig:
        pass

    fake_config_mod.Config = FakeConfig
    sys.modules["hypercorn.config"] = fake_config_mod

    # Fake event loop with add_signal_handler and run_until_complete
    class FakeLoop:
        def __init__(self):
            self._handler = None

        def add_signal_handler(self, sig, handler):
            # record handler and simulate registration
            called["added_signal"] = True
            self._handler = handler

        def run_until_complete(self, _coro):
            # simulate calling the signal handler to trigger shutdown
            if self._handler:
                self._handler()
            return None

    import asyncio as _asyncio

    # Patch the real asyncio module's new_event_loop so app.app uses our FakeLoop
    monkeypatch.setattr(_asyncio, "new_event_loop", lambda: FakeLoop(), raising=False)

    # Stub flask_assets so css.build() is safe
    fake_flask_assets = types.ModuleType("flask_assets")

    class FakeBundle:
        def __init__(self, *a, **kw):
            pass

        def build(self):
            return None

    class FakeEnvironment:
        def __init__(self, app):
            pass

        def register(self, name, bundle):
            return None

    fake_flask_assets.Bundle = FakeBundle
    fake_flask_assets.Environment = FakeEnvironment
    sys.modules["flask_assets"] = fake_flask_assets

    try:
        sys.modules.pop("app.app", None)
        runpy.run_module("app.app", run_name="__main__")
    except Exception:
        # allow any exit/stop behaviour; we only assert our flags
        pass

    assert called["added_signal"] is True
    assert called["stopped"] is True
