"""Tests for the APScheduler adapter and module-level Scheduler helper.

This file contains both unittest.TestCase-based tests that exercise the
module-level singleton behavior and pytest-style function tests that
exercise the APScheduler adapter class.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from app.models import apscheduler as apscheduler_mod
from tests.mocks.mock_scheduler import MockScheduler


class TestScheduler(unittest.TestCase):
    """Unit tests for the module-level Scheduler helper (unittest style)."""

    def setUp(self) -> None:
        # Ensure module-level singleton cleared between tests
        try:
            apscheduler_mod._BG_SCHEDULER = None
        except Exception:
            pass
        self._env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        try:
            apscheduler_mod._BG_SCHEDULER = None
        except Exception:
            pass

    @patch("app.models.apscheduler.BackgroundScheduler")
    def test_get_scheduler_initializes_background_scheduler(self, mock_bg_scheduler):
        os.environ.pop("ONBOARD_DISABLE_SCHEDULER", None)

        mock_instance = MagicMock()
        mock_bg_scheduler.return_value = mock_instance

        scheduler = apscheduler_mod.Scheduler.getScheduler()

        # Should return the instance created by BackgroundScheduler
        self.assertIs(scheduler, mock_instance)
        mock_bg_scheduler.assert_called_once()

    @patch("app.models.apscheduler.BackgroundScheduler")
    def test_get_scheduler_respects_disable_env(self, mock_bg_scheduler):
        # When ONBOARD_DISABLE_SCHEDULER is true, getScheduler should not start
        os.environ["ONBOARD_DISABLE_SCHEDULER"] = "True"

        mock_instance = MagicMock()
        mock_bg_scheduler.return_value = mock_instance

        scheduler = apscheduler_mod.Scheduler.getScheduler()

        self.assertIs(scheduler, mock_instance)
        mock_bg_scheduler.assert_called_once()
        self.assertFalse(mock_instance.start.called)

    def test_shutdown_calls_shutdown_when_running(self):
        # Use MockScheduler to simulate running state
        mock_sched = MockScheduler()
        mock_sched._running = True

        # inject into module-level singleton
        apscheduler_mod._BG_SCHEDULER = mock_sched

        apscheduler_mod.Scheduler.getScheduler()
        apscheduler_mod.Scheduler.shutdown()

        # MockScheduler.shutdown flips running to False
        self.assertFalse(mock_sched.running)

    def test_clear_jobs_calls_remove_all_jobs(self):
        mock_sched = MockScheduler()
        apscheduler_mod._BG_SCHEDULER = mock_sched

        apscheduler_mod.Scheduler.getScheduler()
        apscheduler_mod.Scheduler.clear_jobs()

        # MockScheduler records remove_all_jobs via helper flag
        self.assertTrue(mock_sched._remove_all_called)


# --- migrated from tests/models/test_apscheduler_scheduler.py ---
class RecordSched:
    """A tiny scheduler replacement that records calls for assertions.

    Used by pytest-style tests below.
    """

    def __init__(self):
        self.running = False
        self.last = None

    def add_job(self, func, **kwargs):
        self.last = ("add", func, kwargs)
        return {"id": kwargs.get("id"), "kwargs": kwargs}

    def remove_job(self, job_id, jobstore=None):
        self.last = ("remove", job_id, jobstore)

    def modify_job(self, job_id, **changes):
        self.last = ("modify", job_id, changes)
        return {"modified": job_id, "changes": changes}

    def start(self):
        self.running = True

    def shutdown(self, wait=True):
        """Tests for the APScheduler adapter and module-level Scheduler helper.

        This file contains both unittest.TestCase-based tests that exercise the
        module-level singleton behavior and pytest-style function tests that
        exercise the APScheduler adapter class.
        """

        import os
        import unittest
        from unittest.mock import MagicMock, patch

        from app.models import apscheduler as apscheduler_mod
        from tests.mocks.mock_scheduler import MockScheduler

        class TestScheduler(unittest.TestCase):
            """Unit tests for the module-level Scheduler helper (unittest style)."""

            def setUp(self) -> None:
                # Ensure module-level singleton cleared between tests
                try:
                    apscheduler_mod._BG_SCHEDULER = None
                except Exception:
                    pass
                self._env = dict(os.environ)

            def tearDown(self) -> None:
                os.environ.clear()
                os.environ.update(self._env)
                try:
                    apscheduler_mod._BG_SCHEDULER = None
                except Exception:
                    pass

            @patch("app.models.apscheduler.BackgroundScheduler")
            def test_get_scheduler_initializes_background_scheduler(
                self, mock_bg_scheduler
            ):
                os.environ.pop("ONBOARD_DISABLE_SCHEDULER", None)

                mock_instance = MagicMock()
                mock_bg_scheduler.return_value = mock_instance

                scheduler = apscheduler_mod.Scheduler.getScheduler()

                # Should return the instance created by BackgroundScheduler
                self.assertIs(scheduler, mock_instance)
                mock_bg_scheduler.assert_called_once()

            @patch("app.models.apscheduler.BackgroundScheduler")
            def test_get_scheduler_respects_disable_env(self, mock_bg_scheduler):
                # When ONBOARD_DISABLE_SCHEDULER is true, getScheduler should not start
                os.environ["ONBOARD_DISABLE_SCHEDULER"] = "True"

                mock_instance = MagicMock()
                mock_bg_scheduler.return_value = mock_instance

                scheduler = apscheduler_mod.Scheduler.getScheduler()

                self.assertIs(scheduler, mock_instance)
                mock_bg_scheduler.assert_called_once()
                self.assertFalse(mock_instance.start.called)

            def test_shutdown_calls_shutdown_when_running(self):
                # Use MockScheduler to simulate running state
                mock_sched = MockScheduler()
                mock_sched._running = True

                # inject into module-level singleton
                apscheduler_mod._BG_SCHEDULER = mock_sched

                apscheduler_mod.Scheduler.getScheduler()
                apscheduler_mod.Scheduler.shutdown()

                # MockScheduler.shutdown flips running to False
                self.assertFalse(mock_sched.running)

            def test_clear_jobs_calls_remove_all_jobs(self):
                mock_sched = MockScheduler()
                apscheduler_mod._BG_SCHEDULER = mock_sched

                apscheduler_mod.Scheduler.getScheduler()
                apscheduler_mod.Scheduler.clear_jobs()

                # MockScheduler records remove_all_jobs via helper flag
                self.assertTrue(mock_sched._remove_all_called)

        # --- pytest-style adapter tests helpers ---

        class RecordSched:
            """A tiny scheduler replacement that records calls for assertions."""

            def __init__(self):
                self.running = False
                self.last = None

            def add_job(self, func, **kwargs):
                self.last = ("add", func, kwargs)
                return {"id": kwargs.get("id"), "kwargs": kwargs}

            def remove_job(self, job_id, jobstore=None):
                self.last = ("remove", job_id, jobstore)

            def modify_job(self, job_id, **changes):
                self.last = ("modify", job_id, changes)
                return {"modified": job_id, "changes": changes}

            def start(self):
                self.running = True

            def shutdown(self, wait=True):
                self.running = False

        class FaultySched:
            """A scheduler that raises from its operations to test swallow behavior."""

            def __init__(self):
                self.running = False

            def add_job(self, *a, **k):
                raise RuntimeError("add-fail")

            def remove_job(self, *a, **k):
                raise RuntimeError("remove-fail")

            def modify_job(self, *a, **k):
                raise RuntimeError("modify-fail")

            def start(self):
                raise RuntimeError("start-fail")

            def shutdown(self, wait=True):
                raise RuntimeError("shutdown-fail")

        def test_default_ctor_uses_scheduler_singleton(monkeypatch):
            rec = RecordSched()
            # Patch the classmethod getScheduler to return our recorder
            monkeypatch.setattr(
                apscheduler_mod.Scheduler, "getScheduler", staticmethod(lambda: rec)
            )

            inst = apscheduler_mod.APScheduler()
            # call add_job through default-constructed instance
            res = inst.add_job(lambda: None, id="x", foo=1)
            assert isinstance(res, dict)
            assert rec.last[0] == "add"

        def test_add_remove_modify_forwarding_and_jobstore():
            rec = RecordSched()
            inst = apscheduler_mod.APScheduler(sched=rec)

            inst.add_job(lambda: None, trigger="cron", id="j2", foo="v")
            assert rec.last[0] == "add"
            assert rec.last[2]["trigger"] == "cron"

            inst.remove_job("j2", jobstore="custom")
            assert rec.last[0] == "remove"
            assert rec.last[2] == "custom" or rec.last[1] == "j2"

            inst.add_job(lambda: None, id="j2", foo="v")
            out = inst.modify_job("j2", foo="z")
            assert out["modified"] == "j2"

        def test_start_and_shutdown_swallow_exceptions():
            faulty = FaultySched()
            # when constructed with faulty scheduler, start/shutdown should not raise
            inst = apscheduler_mod.APScheduler(sched=faulty)
            # start should swallow underlying exception
            inst.start()
            # shutdown should swallow underlying exception
            inst.shutdown()

        def test_running_property_reflects_underlying():
            mock_scheduler = MockScheduler()
            inst = apscheduler_mod.APScheduler(sched=mock_scheduler)
            assert inst.running is False
            mock_scheduler._running = True
            assert inst.running is True

        def test_add_remove_modify_and_start_shutdown_delegate():
            mock_scheduler = MockScheduler()
            inst = apscheduler_mod.APScheduler(sched=mock_scheduler)

            res = inst.add_job(lambda: None, trigger="interval", id="j1", foo="bar")
            # MockScheduler returns the stored job dict and records it under the id
            assert isinstance(res, dict)
            assert mock_scheduler.has_job("j1")
            assert res["kwargs"].get("foo") == "bar"

            inst.remove_job("j1")
            assert not mock_scheduler.has_job("j1")

            # add back then modify
            inst.add_job(lambda: None, id="j1", foo="bar")
            modified = inst.modify_job("j1", foo="baz")
            assert modified["kwargs"].get("foo") == "baz"

            # start delegates to underlying scheduler
            mock_scheduler._running = False
            inst.start()
            assert mock_scheduler.running is True

            # shutdown delegates
            inst.shutdown(wait=True)
            assert mock_scheduler.running is False
