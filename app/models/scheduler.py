import os
from apscheduler.schedulers.background import BackgroundScheduler

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Scheduler:
	__scheduler = None

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

			if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
				Scheduler.__scheduler.start()
				logger.info('Scheduler started!')
	
		return Scheduler.__scheduler
