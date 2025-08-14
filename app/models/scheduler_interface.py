from typing import Any, Optional, Protocol


class SchedulerInterface(Protocol):
    """Structural interface for scheduler implementations.

    Using a Protocol allows both concrete implementations and test
    doubles to satisfy the contract by shape rather than nominal
    inheritance. Keep the method signatures compatible with
    APScheduler's API.
    """

    @property
    def running(self) -> bool:  # pragma: no cover - tiny shim
        ...

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
        ...

    def remove_job(self, job_id: str, jobstore: Optional[str] = None) -> None:
        ...

    def modify_job(
        self, job_id: str, jobstore: Optional[str] = None, **changes: Any
    ) -> Any:
        ...

    def start(self, paused: bool = False) -> None:
        ...

    def shutdown(self, wait: bool = True) -> None:
        ...
