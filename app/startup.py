import datetime
import logging
import os
import shutil
from pathlib import Path

from app.models.utils import pwd

logger = logging.getLogger(__name__)


class Startup:
    """Application startup helper.

    Centralizes computation of working and cache directories driven by the
    WORKING_STORAGE environment variable. On import/init this will ensure the
    cache directory exists so other modules can rely on it.
    """

    WORKING_ENV = "WORKING_STORAGE"
    working_dir: Path
    cache_dir: Path

    @classmethod
    def init(cls) -> None:
        # working_dir defaults to a folder named ".working" under repo root (pwd)
        cls.working_dir = pwd.joinpath(os.getenv(cls.WORKING_ENV, ".working")).resolve()
        cls.cache_dir = cls.working_dir.joinpath("cache")
        cls.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_cache_dir(cls) -> Path:
        return cls.cache_dir

    @classmethod
    def archive_large_jsons(cls, min_size_bytes: int = 300 * 1024) -> list[Path]:
        """Move top-level .json files larger than `min_size_bytes` from the
        cache directory into an archive directory named `archive-YYYY-MM-DD`.

        Returns a list of destination paths for moved files.
        """
        moved = []
        cache_dir = cls.get_cache_dir()
        if not cache_dir.exists():
            logger.debug("Cache dir does not exist, nothing to archive: %s", cache_dir)
            return moved

        today_archive = cache_dir.joinpath(
            f"archive-{datetime.date.today().isoformat()}"
        )
        today_archive.mkdir(parents=True, exist_ok=True)

        for entry in cache_dir.iterdir():
            # only top-level files
            if not entry.is_file():
                continue
            if entry.suffix.lower() != ".json":
                continue
            try:
                if entry.stat().st_size > min_size_bytes:
                    logger.info(
                        "Archiving large cache file %s -> %s", entry, today_archive
                    )
                    dest = today_archive.joinpath(entry.name)
                    # use shutil.move to preserve atomic move semantics across filesystems
                    shutil.move(str(entry), str(dest))
                    moved.append(dest)
            except Exception:
                logger.exception("Failed to archive cache file: %s", entry)

        if not moved:
            logger.debug("No large cache files found in %s", cache_dir)

        return moved


def _is_testing_mode() -> bool:
    # Consider testing mode if FLASK_ENV=="testing" or scheduler is explicitly disabled
    if os.environ.get("FLASK_ENV", "").lower() == "testing":
        return True
    if os.environ.get("ONBOARD_DISABLE_SCHEDULER", "False").lower() == "true":
        return True
    return False


# Initialize on import so modules can import and use Startup.get_cache_dir()
Startup.init()

# Run archive on startup by default, unless in testing/disabled scheduler
if (
    os.environ.get("ONBOARD_ARCHIVE_ON_STARTUP", "True").lower() == "true"
    and not _is_testing_mode()
):
    try:
        Startup.archive_large_jsons()
    except Exception:
        logger.exception("Startup archive on import failed")

# Schedule daily archive job in production mode (don't schedule in testing)
try:
    # import Scheduler lazily to avoid circular import issues in tests
    from app.models.scheduler import Scheduler

    sched = Scheduler.getScheduler()
    # Only register the job if the scheduler is running (matches Feed behavior)
    if (
        sched.running
        and os.environ.get("FLASK_ENV", "development").lower() == "production"
    ):
        try:
            sched.add_job(
                Startup.archive_large_jsons,
                "cron",
                hour=0,
                minute=0,
                id="startup_archive_daily",
                replace_existing=True,
                name="Archive large cache JSONs - daily",
            )
        except Exception:
            logger.exception("Failed to schedule daily archive job")
except Exception:
    # If scheduler couldn't be imported or initialized, log but continue
    logger.debug("Scheduler not available for registering daily archive job")
