from app.models.apscheduler_scheduler import APSchedulerScheduler
from tests.mocks.mock_scheduler import MockScheduler


def test_running_property_reflects_underlying():
  mock_scheduler = MockScheduler()
  inst = APSchedulerScheduler(sched=mock_scheduler)
  assert inst.running is False
  mock_scheduler._running = True
  assert inst.running is True


def test_add_remove_modify_and_start_shutdown_delegate():
  mock_scheduler = MockScheduler()
  inst = APSchedulerScheduler(sched=mock_scheduler)

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
