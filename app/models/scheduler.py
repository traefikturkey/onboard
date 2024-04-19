from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR 
from apscheduler.schedulers.background import Event, BackgroundScheduler

import logging

class Scheduler:
	__scheduler = None
	
	def scheduler(self) -> BackgroundScheduler:
		return Scheduler.getScheduler()

	@staticmethod
	def shutdown():
		scheduler = Scheduler.getScheduler()
		if scheduler and scheduler.running:
			scheduler.shutdown()
	 
	@staticmethod
	def	clear_jobs():
		Scheduler.getScheduler().remove_all_jobs()

	@staticmethod
	def getScheduler() -> BackgroundScheduler:
			if Scheduler.__scheduler == None:
				Scheduler.__scheduler = BackgroundScheduler()
				Scheduler.__scheduler.start()
				logging.info('Scheduler started')

				# async def listener(event: Event) -> None:
				# 	print(f"Received {event.__class__.__name__}")
		 
				# def my_listener(event):
				# 	if event.exception:
				# 			print('The job crashed :(')
				# 	else:
				# 			print('The job worked :)' + str(event.job_id))

				# SchedulerWidget.__scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
		
			return Scheduler.__scheduler
