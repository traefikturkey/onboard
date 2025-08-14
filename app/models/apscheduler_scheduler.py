"""APScheduler-backed Scheduler implementation.

This wraps the existing `Scheduler.getScheduler()` singleton so the rest of
the codebase can depend on the `SchedulerInterface` abstraction for easier
testing and injection.
"""
from typing import Any, Optional, Protocol

from .scheduler import Scheduler
from .scheduler_interface import SchedulerInterface


class _SchedLike(Protocol):
    def add_job(self, *args, **kwargs) -> Any:
        ...

    def remove_job(self, *args, **kwargs) -> Any:
        ...

    def modify_job(self, *args, **kwargs) -> Any:
        ...

    def start(self) -> None:
        ...

    def shutdown(self, wait: bool = True) -> None:
        ...

    @property
    def running(self) -> bool:
        ...


class APSchedulerScheduler(SchedulerInterface):
    """Concrete SchedulerInterface using APScheduler's BackgroundScheduler.

    This implementation delegates to the project's singleton Scheduler
    instance (defined in `app/models/scheduler.py`) to preserve the
    existing startup/shutdown semantics and environment-based disabling used
    across the app.
    """

    def __init__(self, sched: Optional[_SchedLike] = None) -> None:
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
        # Delegate to underlying scheduler's add_job. Let APScheduler raise
        # its own errors for invalid args; this class keeps the signature
        # compatible with SchedulerInterface.
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
        # APScheduler's BackgroundScheduler.start() doesn't accept a `paused`
        # parameter, so we ignore it here to keep the interface compatible.
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
