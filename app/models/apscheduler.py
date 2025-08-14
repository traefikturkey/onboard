import os
from typing import Any, Optional

from apscheduler.schedulers.background import BackgroundScheduler

from .scheduler_interface import SchedulerInterface

# BackgroundScheduler singleton and helpers (migrated from old scheduler.py)
_BG_SCHEDULER: Optional[BackgroundScheduler] = None


def _create_background_scheduler() -> BackgroundScheduler:
    return BackgroundScheduler(
        {
            "apscheduler.executors.default": {
                "class": "apscheduler.executors.pool:ThreadPoolExecutor",
                "max_workers": "5",
            },
            "apscheduler.executors.processpool": {
                "class": "apscheduler.executors.pool:ThreadPoolExecutor",
                "max_workers": "20",
            },
        }
    )


class Scheduler:
    """Compatibility small wrapper exposing the familiar static API.

    This preserves the former `app.models.scheduler.Scheduler` behavior while
    keeping the concrete APScheduler adapter in the same module (so we can
    delete the old files).
    """

    @staticmethod
    def shutdown():
        sched = Scheduler.getScheduler()
        if sched and getattr(sched, "running", False):
            sched.shutdown()

    @staticmethod
    def clear_jobs():
        Scheduler.getScheduler().remove_all_jobs()

    @staticmethod
    def start():
        if _BG_SCHEDULER:
            _BG_SCHEDULER.start()

    @staticmethod
    def getScheduler() -> BackgroundScheduler:
        global _BG_SCHEDULER
        if _BG_SCHEDULER is None:
            _BG_SCHEDULER = _create_background_scheduler()

            # Check if scheduler is disabled for testing
            if os.environ.get("ONBOARD_DISABLE_SCHEDULER", "False").lower() == "true":
                # Don't start scheduler when disabled
                pass
            else:
                # Start scheduler unless explicitly disabled
                # In Flask dev mode with auto-reload, only start on main process
                flask_env = os.environ.get("FLASK_ENV", "development")
                is_dev_mode = flask_env == "development"
                is_main_process = bool(os.environ.get("WERKZEUG_RUN_MAIN"))
                
                if is_dev_mode and not is_main_process:
                    # In development mode but not main process (reloader process)
                    # Start scheduler anyway since we may not be using Werkzeug reloader
                    if _BG_SCHEDULER and not _BG_SCHEDULER.running:
                        Scheduler.start()
                elif _BG_SCHEDULER and not _BG_SCHEDULER.running:
                    Scheduler.start()

        return _BG_SCHEDULER


# Adapter and Protocol (migrated from apscheduler_scheduler.py)


class APScheduler(SchedulerInterface):
    """Concrete SchedulerInterface using APScheduler's BackgroundScheduler.

    This implementation delegates to the project's singleton BackgroundScheduler
    by default but accepts an injected scheduler for tests.
    """

    def __init__(self, sched: Optional[SchedulerInterface] = None) -> None:
        # Allow injecting a scheduler (useful for tests). Default to the
        # project's singleton BackgroundScheduler for runtime behaviour.
        self._sched = sched or Scheduler.getScheduler()

    @property
    def running(self) -> bool:
        try:
            return bool(self._sched and getattr(self._sched, "running", False))
        except Exception:
            return False

    def add_job(
        self,
        func: Any,
        trigger: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        misfire_grace_time: Optional[int] = None,
        coalesce: Optional[bool] = None,
        max_instances: Optional[int] = None,
        next_run_time: Optional[Any] = None,
        jobstore: Optional[str] = None,
        executor: Optional[str] = None,
        replace_existing: bool = False,
        **trigger_args: Any,
    ) -> Any:
        return self._sched.add_job(
            func,
            trigger=trigger,
            args=args or (),
            kwargs=kwargs or {},
            id=id,
            name=name,
            misfire_grace_time=misfire_grace_time,
            coalesce=coalesce,
            max_instances=max_instances,
            next_run_time=next_run_time,
            jobstore=jobstore,
            executor=executor,
            replace_existing=replace_existing,
            **trigger_args,
        )

    def remove_job(self, job_id: str, jobstore: Optional[str] = None) -> None:
        if jobstore:
            return self._sched.remove_job(job_id, jobstore)
        return self._sched.remove_job(job_id)

    def modify_job(
        self, job_id: str, jobstore: Optional[str] = None, **changes: Any
    ) -> Any:
        if jobstore:
            return self._sched.modify_job(job_id, jobstore=jobstore, **changes)
        return self._sched.modify_job(job_id, **changes)

    def start(self, paused: bool = False) -> None:
        if not getattr(self._sched, "running", False):
            try:
                self._sched.start()
            except Exception:
                # Preserve behavior: do not crash if scheduler can't start
                pass

    def shutdown(self, wait: bool = True) -> None:
        try:
            if getattr(self._sched, "running", False):
                self._sched.shutdown(wait=wait)
        except Exception:
            # Swallow shutdown errors to match existing graceful shutdown
            # approach in the project.
            pass
