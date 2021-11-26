from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from pytz import utc, timezone
from datetime import datetime, timedelta
import os

from config import settings
from log_config import logger
from tesla import tesla_preheat

TZ = os.getenv('TZ') or utc


class Scheduler:
    def __init__(self):
        self.bgscheduler = BackgroundScheduler(timezone=TZ)
        self.bgscheduler.start()
        self.configure()

    def configure(self):
        days = settings.get('schedule', 'days_of_week')
        if days != '' and settings.getboolean('general', 'enabled') and tesla_preheat.session.authorized:
            self.bgscheduler.add_job(tesla_preheat.start_preheat,
                                     'cron',
                                     day_of_week=days,
                                     hour=settings.get('schedule', 'start_time').split(':')[0],
                                     minute=settings.get('schedule', 'start_time').split(':')[1],
                                     id='start_preheat',
                                     replace_existing=True)
            logger.info('Next preheating will occur at %s',
                        self.bgscheduler.get_job('start_preheat').next_run_time)
        else:
            try:
                self.bgscheduler.remove_job(job_id='start_preheat')
            except JobLookupError:
                pass
            finally:
                logger.info('Vehicle cabin automatic heating not requested, you\'re not authenticated or no days have '
                            'been scheduled.')

    def add_stop_job(self):
        # Add job to stop the preheating
        end_time = datetime.now(timezone(TZ)) + timedelta(minutes=settings.getint('schedule', 'duration'))
        logger.info('Scheduling preheating end job at %s', end_time.strftime("%m/%d/%Y, %H:%M:%S"))
        self.bgscheduler.add_job(tesla_preheat.stop_preheat,
                                 'date',
                                 next_run_time=end_time,
                                 id='stop_preheat',
                                 replace_existing=True)


scheduler = Scheduler()
