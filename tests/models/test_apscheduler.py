"""Tests for APScheduler module."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestSchedulerStaticMethods:
    """Test Scheduler static methods."""

    def test_shutdown_does_nothing_when_no_scheduler(self):
        """Test shutdown is safe when no scheduler exists."""
        from app.models.apscheduler import Scheduler

        with patch.object(Scheduler, "getScheduler", return_value=None):
            # Should not raise
            Scheduler.shutdown()

    def test_shutdown_calls_shutdown_on_running_scheduler(self):
        """Test shutdown calls shutdown on running scheduler."""
        from app.models.apscheduler import Scheduler

        mock_sched = MagicMock()
        mock_sched.running = True

        with patch.object(Scheduler, "getScheduler", return_value=mock_sched):
            Scheduler.shutdown()
            mock_sched.shutdown.assert_called_once()

    def test_shutdown_swallows_exceptions(self):
        """Test shutdown swallows exceptions gracefully."""
        from app.models.apscheduler import Scheduler

        mock_sched = MagicMock()
        mock_sched.running = True
        mock_sched.shutdown.side_effect = Exception("Shutdown error")

        with patch.object(Scheduler, "getScheduler", return_value=mock_sched):
            # Should not raise
            Scheduler.shutdown()

    def test_clear_jobs_does_nothing_when_no_scheduler(self):
        """Test clear_jobs is safe when no scheduler exists."""
        from app.models.apscheduler import Scheduler

        with patch.object(Scheduler, "getScheduler", return_value=None):
            # Should not raise
            Scheduler.clear_jobs()

    def test_clear_jobs_removes_all_jobs(self):
        """Test clear_jobs removes all jobs from scheduler."""
        from app.models.apscheduler import Scheduler

        mock_sched = MagicMock()

        with patch.object(Scheduler, "getScheduler", return_value=mock_sched):
            Scheduler.clear_jobs()
            mock_sched.remove_all_jobs.assert_called_once()

    def test_clear_jobs_swallows_exceptions(self):
        """Test clear_jobs swallows exceptions gracefully."""
        from app.models.apscheduler import Scheduler

        mock_sched = MagicMock()
        mock_sched.remove_all_jobs.side_effect = Exception("Clear error")

        with patch.object(Scheduler, "getScheduler", return_value=mock_sched):
            # Should not raise
            Scheduler.clear_jobs()

    def test_start_does_nothing_when_no_scheduler(self):
        """Test start is safe when _BG_SCHEDULER is None."""
        from app.models import apscheduler

        original = apscheduler._BG_SCHEDULER
        try:
            apscheduler._BG_SCHEDULER = None
            # Should not raise
            apscheduler.Scheduler.start()
        finally:
            apscheduler._BG_SCHEDULER = original

    def test_start_calls_start_on_scheduler(self):
        """Test start calls start on the background scheduler."""
        from app.models import apscheduler

        mock_sched = MagicMock()
        original = apscheduler._BG_SCHEDULER
        try:
            apscheduler._BG_SCHEDULER = mock_sched
            apscheduler.Scheduler.start()
            mock_sched.start.assert_called_once()
        finally:
            apscheduler._BG_SCHEDULER = original


class TestAPSchedulerAdapter:
    """Test APScheduler adapter class."""

    def test_init_with_injected_scheduler(self):
        """Test APScheduler can use injected scheduler."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        adapter = APScheduler(sched=mock_sched)
        assert adapter._sched is mock_sched

    def test_running_property_returns_false_when_no_scheduler(self):
        """Test running property returns False when scheduler is None."""
        from app.models.apscheduler import APScheduler

        adapter = APScheduler(sched=None)
        assert adapter.running is False

    def test_running_property_returns_scheduler_running_state(self):
        """Test running property reflects scheduler state."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.running = True
        adapter = APScheduler(sched=mock_sched)
        assert adapter.running is True

        mock_sched.running = False
        assert adapter.running is False

    def test_running_property_handles_exception(self):
        """Test running property returns False on exception."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        type(mock_sched).running = property(lambda self: (_ for _ in ()).throw(Exception("Error")))
        adapter = APScheduler(sched=mock_sched)
        assert adapter.running is False

    def test_add_job_delegates_to_scheduler(self):
        """Test add_job delegates to underlying scheduler."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.add_job.return_value = "job_id"
        adapter = APScheduler(sched=mock_sched)

        def dummy_func():
            pass

        result = adapter.add_job(
            dummy_func,
            trigger="interval",
            args=(1,),
            kwargs={"key": "value"},
            id="test_job",
            name="Test Job",
        )

        mock_sched.add_job.assert_called_once()
        assert result == "job_id"

    def test_remove_job_delegates_to_scheduler(self):
        """Test remove_job delegates to underlying scheduler."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        adapter = APScheduler(sched=mock_sched)

        adapter.remove_job("job_id")
        mock_sched.remove_job.assert_called_with("job_id")

    def test_remove_job_with_jobstore(self):
        """Test remove_job passes jobstore parameter."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        adapter = APScheduler(sched=mock_sched)

        adapter.remove_job("job_id", jobstore="memory")
        mock_sched.remove_job.assert_called_with("job_id", "memory")

    def test_modify_job_delegates_to_scheduler(self):
        """Test modify_job delegates to underlying scheduler."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        adapter = APScheduler(sched=mock_sched)

        adapter.modify_job("job_id", next_run_time=None)
        mock_sched.modify_job.assert_called_with("job_id", next_run_time=None)

    def test_modify_job_with_jobstore(self):
        """Test modify_job passes jobstore parameter."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        adapter = APScheduler(sched=mock_sched)

        adapter.modify_job("job_id", jobstore="memory", next_run_time=None)
        mock_sched.modify_job.assert_called_with(
            "job_id", jobstore="memory", next_run_time=None
        )

    def test_start_starts_scheduler_when_not_running(self):
        """Test start starts the scheduler if not already running."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.running = False
        adapter = APScheduler(sched=mock_sched)

        adapter.start()
        mock_sched.start.assert_called_once()

    def test_start_does_not_start_if_already_running(self):
        """Test start does not start scheduler if already running."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.running = True
        adapter = APScheduler(sched=mock_sched)

        adapter.start()
        mock_sched.start.assert_not_called()

    def test_start_swallows_exceptions(self):
        """Test start swallows exceptions gracefully."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.running = False
        mock_sched.start.side_effect = Exception("Start error")
        adapter = APScheduler(sched=mock_sched)

        # Should not raise
        adapter.start()

    def test_shutdown_shuts_down_running_scheduler(self):
        """Test shutdown shuts down the scheduler if running."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.running = True
        adapter = APScheduler(sched=mock_sched)

        adapter.shutdown(wait=False)
        mock_sched.shutdown.assert_called_with(wait=False)

    def test_shutdown_does_not_shutdown_if_not_running(self):
        """Test shutdown does not shutdown if not running."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.running = False
        adapter = APScheduler(sched=mock_sched)

        adapter.shutdown()
        mock_sched.shutdown.assert_not_called()

    def test_shutdown_swallows_exceptions(self):
        """Test shutdown swallows exceptions gracefully."""
        from app.models.apscheduler import APScheduler

        mock_sched = MagicMock()
        mock_sched.running = True
        mock_sched.shutdown.side_effect = Exception("Shutdown error")
        adapter = APScheduler(sched=mock_sched)

        # Should not raise
        adapter.shutdown()


class TestCreateBackgroundScheduler:
    """Test _create_background_scheduler function."""

    def test_returns_none_when_apscheduler_not_available(self):
        """Test returns None when BackgroundScheduler is None."""
        from app.models import apscheduler

        original = apscheduler.BackgroundScheduler
        try:
            apscheduler.BackgroundScheduler = None
            result = apscheduler._create_background_scheduler()
            assert result is None
        finally:
            apscheduler.BackgroundScheduler = original


class TestGetSchedulerStartupLogic:
    """Test Scheduler.getScheduler startup logic."""

    def test_scheduler_not_started_in_test_environment(self):
        """Test scheduler is not started when in test environment."""
        from app.models import apscheduler

        # Reset the global scheduler
        original = apscheduler._BG_SCHEDULER
        try:
            apscheduler._BG_SCHEDULER = None

            with patch("app.models.apscheduler.is_test_environment", return_value=True):
                with patch.object(apscheduler.Scheduler, "start") as mock_start:
                    apscheduler.Scheduler.getScheduler()
                    mock_start.assert_not_called()
        finally:
            apscheduler._BG_SCHEDULER = original

    def test_scheduler_not_started_when_disabled(self):
        """Test scheduler is not started when ONBOARD_DISABLE_SCHEDULER=true."""
        from app.models import apscheduler

        original = apscheduler._BG_SCHEDULER
        original_env = os.environ.get("ONBOARD_DISABLE_SCHEDULER")
        try:
            apscheduler._BG_SCHEDULER = None
            os.environ["ONBOARD_DISABLE_SCHEDULER"] = "true"

            with patch("app.models.apscheduler.is_test_environment", return_value=False):
                with patch.object(apscheduler.Scheduler, "start") as mock_start:
                    apscheduler.Scheduler.getScheduler()
                    mock_start.assert_not_called()
        finally:
            apscheduler._BG_SCHEDULER = original
            if original_env is None:
                os.environ.pop("ONBOARD_DISABLE_SCHEDULER", None)
            else:
                os.environ["ONBOARD_DISABLE_SCHEDULER"] = original_env
