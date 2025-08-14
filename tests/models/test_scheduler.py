from app.models.scheduler import Scheduler
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestScheduler(unittest.TestCase):
  def setUp(self):
    # Ensure Scheduler singleton is cleared between tests
    try:
      Scheduler._Scheduler__scheduler = None
    except Exception:
      # If attribute doesn't exist, ignore
      pass
    # Save environment
    self._env = dict(os.environ)

  def tearDown(self):
    # Restore environment
    os.environ.clear()
    os.environ.update(self._env)
    # Clear scheduler singleton again
    try:
      Scheduler._Scheduler__scheduler = None
    except Exception:
      pass

  @patch("app.models.scheduler.BackgroundScheduler")
  def test_get_scheduler_initializes_background_scheduler(self, mock_bg_scheduler):
    # Ensure environment is clean
    os.environ.pop("ONBOARD_DISABLE_SCHEDULER", None)

    mock_instance = MagicMock()
    mock_bg_scheduler.return_value = mock_instance

    scheduler = Scheduler.getScheduler()

    # Should return the instance created by BackgroundScheduler
    self.assertIs(scheduler, mock_instance)
    mock_bg_scheduler.assert_called_once()

  @patch("app.models.scheduler.BackgroundScheduler")
  def test_get_scheduler_respects_disable_env(self, mock_bg_scheduler):
    # When ONBOARD_DISABLE_SCHEDULER is true, getScheduler still returns an instance
    # but it should not attempt to start the scheduler (start() won't be called)
    # set the disable flag
    os.environ["ONBOARD_DISABLE_SCHEDULER"] = "True"

    mock_instance = MagicMock()
    mock_bg_scheduler.return_value = mock_instance

    scheduler = Scheduler.getScheduler()

    self.assertIs(scheduler, mock_instance)
    mock_bg_scheduler.assert_called_once()

    # start should not have been called automatically by getScheduler
    self.assertFalse(mock_instance.start.called)

  @patch("app.models.scheduler.BackgroundScheduler")
  def test_shutdown_calls_shutdown_when_running(self, mock_bg_scheduler):
    mock_instance = MagicMock()
    mock_instance.running = True
    mock_bg_scheduler.return_value = mock_instance

    Scheduler.getScheduler()
    Scheduler.shutdown()

    mock_instance.shutdown.assert_called_once()

  @patch("app.models.scheduler.BackgroundScheduler")
  def test_clear_jobs_calls_remove_all_jobs(self, mock_bg_scheduler):
    mock_instance = MagicMock()
    mock_bg_scheduler.return_value = mock_instance

    Scheduler.getScheduler()
    Scheduler.clear_jobs()

    mock_instance.remove_all_jobs.assert_called_once()


if __name__ == "__main__":
  unittest.main()
