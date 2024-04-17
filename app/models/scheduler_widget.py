from datetime import datetime
from models.widget import Widget
from apscheduler.schedulers.background import BackgroundScheduler

class SchedulerWidget(Widget):
	__scheduler = None
 
	def __init__(self, widget: dict):
		super().__init__(widget)
	
	@property
	def scheduler(self):
		return SchedulerWidget.getScheduler()
 
	@staticmethod
	def getScheduler():
			if SchedulerWidget.__scheduler == None:
				SchedulerWidget.__scheduler = BackgroundScheduler()
				SchedulerWidget.__scheduler.start()
				print(f'[{datetime.now()}] Scheduler started')
			return SchedulerWidget.__scheduler