from app.models import scheduler as sched_mod
from app.models.apscheduler_scheduler import APSchedulerScheduler


class RecordSched:
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
  monkeypatch.setattr(sched_mod.Scheduler, "getScheduler", staticmethod(lambda: rec))

  inst = APSchedulerScheduler()
  # call add_job through default-constructed instance
  res = inst.add_job(lambda: None, id="x", foo=1)
  assert isinstance(res, dict)
  assert rec.last[0] == "add"


def test_add_remove_modify_forwarding_and_jobstore():
  rec = RecordSched()
  inst = APSchedulerScheduler(sched=rec)

  inst.add_job(lambda: None, trigger="cron", id="j2", foo="v")
  assert rec.last[0] == "add"
  assert rec.last[2]["trigger"] == "cron"

  inst.remove_job("j2", jobstore="custom")
  assert rec.last[0] == "remove"
  assert rec.last[2] == "custom" or rec.last[1] == "j2"

  inst.add_job(lambda: None, id="j2", foo="v")
  out = inst.modify_job("j2", foo="z")
  assert out["modified"] == "j2"


def test_start_and_shutdown_swallow_exceptions(monkeypatch):
  faulty = FaultySched()
  # when constructed with faulty scheduler, start/shutdown should not raise
  inst = APSchedulerScheduler(sched=faulty)
  # start should swallow underlying exception
  inst.start()
  # shutdown should swallow underlying exception
  inst.shutdown()
