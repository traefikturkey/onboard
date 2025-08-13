import os

from apscheduler.schedulers.background import BackgroundScheduler


class Scheduler:
    __scheduler = None

    @staticmethod
    def shutdown():
        scheduler = Scheduler.getScheduler()
        if scheduler and scheduler.running:
            scheduler.shutdown()

    @staticmethod
    def clear_jobs():
        Scheduler.getScheduler().remove_all_jobs()

    @staticmethod
    def start():
        Scheduler.__scheduler.start()

    @staticmethod
    def getScheduler() -> BackgroundScheduler:
        if Scheduler.__scheduler is None:
            Scheduler.__scheduler = BackgroundScheduler(
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

            if bool(os.environ.get("FLASK_ENV", "development") == "development"):
                if bool(os.environ.get("WERKZEUG_RUN_MAIN")):
                    Scheduler.start()
            elif not Scheduler.__scheduler.running:
                Scheduler.start()

        return Scheduler.__scheduler
