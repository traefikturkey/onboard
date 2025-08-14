from typing import Any, Dict, List, Optional

from app.models.scheduler_interface import SchedulerInterface


class MockScheduler(SchedulerInterface):
    """A simple in-memory scheduler mock that records calls for assertions.

    It never starts background threads and exposes helpers for tests to
    assert jobs were registered/removed.
    """

    def __init__(self) -> None:
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def add_job(self, *args, id: Optional[str] = None, **kwargs) -> Any:
        job_id = id or f"job-{len(self.jobs) + 1}"
        self.jobs[job_id] = {"args": args, "kwargs": kwargs}
        return self.jobs[job_id]

    def remove_job(self, job_id: str, jobstore: Optional[str] = None) -> None:
        if job_id in self.jobs:
            del self.jobs[job_id]

    def modify_job(
        self, job_id: str, jobstore: Optional[str] = None, **changes: Any
    ) -> Any:
        if job_id not in self.jobs:
            raise KeyError(job_id)
        self.jobs[job_id]["kwargs"].update(changes)
        return self.jobs[job_id]

    def start(self, paused: bool = False) -> None:
        self._running = True

    def shutdown(self, wait: bool = True) -> None:
        self._running = False

    # Test helpers
    def has_job(self, job_id: str) -> bool:
        return job_id in self.jobs

    def list_jobs(self) -> List[str]:
        return list(self.jobs.keys())
