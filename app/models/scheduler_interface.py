from abc import ABC, abstractmethod
from typing import Any, Optional


class SchedulerInterface(ABC):
    """Abstract interface for scheduler implementations.

    This allows dependency injection and easier unit testing by providing
    a common interface that can be implemented by both real schedulers
    (APScheduler) and mock schedulers for testing.
    """

    @property
    @abstractmethod
    def running(self) -> bool:
        """Returns True if the scheduler is currently running."""
        pass

    @abstractmethod
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
        """Add a job to the scheduler.

        Args match APScheduler's add_job method signature for compatibility.
        Returns a job object (implementation-specific).
        """
        pass

    @abstractmethod
    def remove_job(self, job_id: str, jobstore: Optional[str] = None) -> None:
        """Remove a job from the scheduler by ID."""
        pass

    @abstractmethod
    def modify_job(
        self, job_id: str, jobstore: Optional[str] = None, **changes: Any
    ) -> Any:
        """Modify an existing job's properties.

        Returns the modified job object (implementation-specific).
        """
        pass

    @abstractmethod
    def start(self, paused: bool = False) -> None:
        """Start the scheduler."""
        pass

    @abstractmethod
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the scheduler."""
        pass
