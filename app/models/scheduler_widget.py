from models.widget import Widget
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR 
from apscheduler.schedulers.background import Event, BackgroundScheduler

import logging

class SchedulerWidget(Widget):
	__scheduler = None
 
	def __init__(self, widget: dict):
		super().__init__(widget)
	
	@property
	def scheduler(self):
		return SchedulerWidget.getScheduler()
 
	@staticmethod
	def getScheduler() -> BackgroundScheduler:
			if SchedulerWidget.__scheduler == None:
				SchedulerWidget.__scheduler = BackgroundScheduler()
				SchedulerWidget.__scheduler.start()
				logging.info('Scheduler started')

				async def listener(event: Event) -> None:
					print(f"Received {event.__class__.__name__}")
     
				# def my_listener(event):
				# 	if event.exception:
				# 			print('The job crashed :(')
				# 	else:
				# 			print('The job worked :)' + str(event.job_id))

				# SchedulerWidget.__scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
			return SchedulerWidget.__scheduler