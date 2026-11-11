import runpy
from unittest.mock import MagicMock

import pytest
from flask import Flask


@pytest.mark.parametrize("debug, expected", [("True", True), ("False", False)])
def test_main_uses_factory_and_parses_debug(monkeypatch, debug, expected):
    app = Flask(__name__)
    app.run = MagicMock()
    create = MagicMock(return_value=app)
    shutdown = MagicMock()
    monkeypatch.setattr("app.factory.create_app", create)
    monkeypatch.setattr("app.models.apscheduler.Scheduler.shutdown", shutdown)
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("FLASK_DEBUG", debug)
    monkeypatch.setenv("ONBOARD_PORT", "9830")
    with pytest.raises(SystemExit):
        runpy.run_module("app.main", run_name="__main__")
    create.assert_called_once_with()
    app.run.assert_called_once_with(port=9830, debug=expected)
    shutdown.assert_called_once_with()


def test_main_production_hypercorn_shutdown(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr("app.factory.create_app", lambda: app)
    shutdown = MagicMock()
    monkeypatch.setattr("app.models.apscheduler.Scheduler.shutdown", shutdown)
    monkeypatch.setenv("FLASK_ENV", "production")
    served = {}

    async def serve(app, config, shutdown_trigger):
        served["app"] = app
        await shutdown_trigger()

    monkeypatch.setattr("hypercorn.asyncio.serve", serve)

    class Loop:
        def add_signal_handler(self, signal, handler):
            self.handler = handler

        def run_until_complete(self, coroutine):
            self.handler()
            # The shutdown event is set, so this coroutine completes synchronously.
            with pytest.raises(StopIteration):
                coroutine.send(None)

    monkeypatch.setattr("asyncio.new_event_loop", Loop)
    runpy.run_module("app.main", run_name="__main__")
    assert served["app"] is app
    shutdown.assert_called_once_with()
