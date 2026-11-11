"""Runtime entry point using the same application factory as the test suite."""

import asyncio
import logging
import os
import signal
import sys
from typing import Any

from app.factory import create_app
from app.models.apscheduler import Scheduler

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.WARN)
logger = logging.getLogger(__name__)

app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", os.environ.get("ONBOARD_PORT", 9830)))
    development = os.environ.get("FLASK_ENV", "development") == "development"
    if development:
        debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
        app.run(port=port, debug=debug)
        Scheduler.shutdown()
        sys.exit()
    else:
        try:
            from hypercorn.asyncio import serve
            from hypercorn.config import Config

            shutdown_event = asyncio.Event()

            def _signal_handler(*_: Any) -> None:
                logger.info("Shutting down...")
                Scheduler.shutdown()
                shutdown_event.set()

            config = Config()
            config.accesslog = "-"
            config.errorlog = "-"
            config.loglevel = "DEBUG"
            config.bind = f"0.0.0.0:{port}"
            loop = asyncio.new_event_loop()
            loop.add_signal_handler(signal.SIGTERM, _signal_handler)

            async def _shutdown_trigger() -> None:
                await shutdown_event.wait()

            loop.run_until_complete(
                serve(app, config, shutdown_trigger=_shutdown_trigger)
            )
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            Scheduler.shutdown()
            sys.exit()
