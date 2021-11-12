import teslapy
import os
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc, timezone
from datetime import datetime, timedelta
import logging
import sys
import time

import requests
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask, AnticatpchaException
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logging.getLogger("apscheduler").setLevel(logging.WARNING)

TZ = os.getenv('TZ') or utc

# Possible boolean values in the configuration.
BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True, 1: True, True: True,
                  '0': False, 'no': False, 'false': False, 'off': False, 0: False, False: False}


class ConfigError(Exception):
    pass


class CaptchaError(Exception):
    pass


class ParsingError(Exception):
    pass


class TeslaPreHeat:
    def __init__(self):
        self.EMAIL = os.getenv('EMAIL') or None
        self.PASSWORD = os.getenv('PASSWORD') or None
        self.ANTI_CAPTCHA_APIKEY = os.getenv('ANTI_CAPTCHA_APIKEY') or None

        self.PREHEAT_DAY_OF_WEEK = os.getenv('PREHEAT_DAY_OF_WEEK') or None
        self.PREHEAT_HOUR = int(os.getenv('PREHEAT_HOUR')) or None
        self.PREHEAT_MINUTE = int(os.getenv('PREHEAT_MINUTE')) or None
        self.PREHEAT_DURATION = int(os.getenv('PREHEAT_DURATION')) or None

        self.DRIVER_TEMP = int(os.getenv('DRIVER_TEMP')) if os.getenv('DRIVER_TEMP') else None
        self.PASSENGER_TEMP = int(os.getenv('PASSENGER_TEMP')) if os.getenv('PASSENGER_TEMP') else None
        self.CABIN_PREHEAT_ENABLED = convert_to_boolean(os.getenv('CABIN_PREHEAT_ENABLED')) if \
            os.getenv('CABIN_PREHEAT_ENABLED') else False
        self.MAX_DEFROST = convert_to_boolean(os.getenv('MAX_DEFROST')) if os.getenv('MAX_DEFROST') else False

        self.DRIVER_SEAT_TEMP = int(os.getenv('DRIVER_SEAT_TEMP')) if os.getenv('DRIVER_SEAT_TEMP') else None
        self.DRIVER_SEAT_ENABLED = convert_to_boolean(os.getenv('DRIVER_SEAT_ENABLED')) if \
            os.getenv('DRIVER_SEAT_ENABLED') else False
        self.PASSENGER_SEAT_TEMP = int(os.getenv('PASSENGER_SEAT_TEMP')) if os.getenv('PASSENGER_SEAT_TEMP') else None
        self.PASSENGER_SEAT_ENABLED = convert_to_boolean(os.getenv('PASSENGER_SEAT_ENABLED')) if \
            os.getenv('PASSENGER_SEAT_ENABLED') else False
        self.REAR_DRIVER_SIDE_SEAT_TEMP = int(os.getenv('REAR_DRIVER_SIDE_SEAT_TEMP')) if \
            os.getenv('REAR_DRIVER_SIDE_SEAT_TEMP') else None
        self.REAR_DRIVER_SIDE_SEAT_ENABLED = convert_to_boolean(os.getenv('REAR_DRIVER_SIDE_SEAT_ENABLED')) if \
            os.getenv('REAR_DRIVER_SIDE_SEAT_ENABLED') else False
        self.REAR_CENTER_SEAT_TEMP = int(os.getenv('REAR_CENTER_SEAT_TEMP')) if os.getenv('REAR_CENTER_SEAT_TEMP') \
            else None
        self.REAR_CENTER_SEAT_ENABLED = convert_to_boolean(os.getenv('REAR_CENTER_SEAT_ENABLED')) if \
            os.getenv('REAR_CENTER_SEAT_ENABLED') else False
        self.REAR_PASSENGER_SIDE_SEAT_TEMP = int(os.getenv('REAR_PASSENGER_SIDE_SEAT_TEMP')) if \
            os.getenv('REAR_PASSENGER_SIDE_SEAT_TEMP') else None
        self.REAR_PASSENGER_SIDE_SEAT_ENABLED = convert_to_boolean(os.getenv('REAR_PASSENGER_SIDE_SEAT_ENABLED')) if \
            os.getenv('REAR_PASSENGER_SIDE_SEAT_ENABLED') else False

        logger.info('Trying to refresh token...')
        self.session = teslapy.Tesla(self.EMAIL, authenticator=self.captcha_solver,
                                     cache_file=os.path.join(os.path.join(os.path.dirname(__file__),
                                                                          'config',
                                                                          'cache.json')))
        
        try:
            logger.info('Retrieving vehicle...')
            self.vehicle = self.session.vehicle_list()[0]
            logger.info('Selected vehicle name: %s', self.vehicle['display_name'])
        except teslapy.HTTPError as e:
            logger.exception(e)

    def captcha_solver(self, login_url):
        api_key = self.ANTI_CAPTCHA_APIKEY
        if not api_key:
            raise ConfigError('Missing anti-captcha.com APIKEY environment variable.')

        logging.info('Trying to solve reCaptcha...')
        session = requests.Session()

        login_page_content = session.get(login_url)
        login_page_content.raise_for_status()

        try:
            sitekey = re.search(r".*sitekey.* : '(.*)'", login_page_content.text).group(1)
            csrf = re.search(r'name="_csrf".+value="([^"]+)"', login_page_content.text).group(1)
            transaction_id = re.search(r'name="transaction_id".+value="([^"]+)"', login_page_content.text).group(1)
        except AttributeError:
            raise ParsingError

        try:
            client = AnticaptchaClient(api_key)
            task = NoCaptchaTaskProxylessTask(login_url, sitekey, is_invisible=True)
            job = client.createTask(task)
            job.join()
            solved_captcha = job.get_solution_response()
        except AnticatpchaException:
            raise CaptchaError
        else:
            post_url = 'https://auth.tesla.com/oauth2/v3/authorize?client_id=ownerapi&response_type=code&' \
                       'scope=openid email offline_access&redirect_uri=https://auth.tesla.com/void/callback&' \
                       'state=tesla_exporter'
            headers = {
                'referer': post_url
            }
            data = {
                'identity': self.EMAIL,
                'credential': self.PASSWORD,
                '_csrf': csrf,
                '_phase': 'authenticate',
                '_process': '1',
                'transaction_id': transaction_id,
                'cancel': '',
                'g-recaptcha-response': solved_captcha,
                'recaptcha': solved_captcha,
            }

            result = session.post(post_url, data, headers=headers, allow_redirects=True)

            if hasattr(result, 'url'):
                logging.info('reCaptcha solved. Continuing login process.')
                return result.url
            else:
                raise CaptchaError

    def start_preheat(self):
        self.wake_vehicle()
    
        # Cabin heater
        if self.CABIN_PREHEAT_ENABLED and self.DRIVER_TEMP and self.PASSENGER_TEMP:
            logger.info('Starting cabin heater...')
            self.vehicle.command('CHANGE_CLIMATE_TEMPERATURE_SETTING', driver_temp=self.DRIVER_TEMP,
                                 passenger_temp=self.PASSENGER_TEMP)
            logger.info('Vehicle cabin heater started')
        else:
            logger.info('Vehicle cabin heating not requested; skipping.')
        self.vehicle.command('CLIMATE_ON')

        # Max defrost
        if self.MAX_DEFROST:
            logger.info('Starting max defrost...')
            self.vehicle.command('MAX_DEFROST', on='true')
            logger.info('Max defrost started')
        else:
            self.vehicle.command('MAX_DEFROST', on='false')
            logger.info('Vehicle cabin heating not requested; skipping.')

        # Driver seat heater
        if self.DRIVER_SEAT_ENABLED and isinstance(self.DRIVER_SEAT_TEMP, int):
            logger.info('Starting driver seat heater')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=0, level=self.DRIVER_SEAT_TEMP)
        elif not self.DRIVER_SEAT_ENABLED or not isinstance(self.DRIVER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=0, level=0)

        # Passenger seat heater
        if self.PASSENGER_SEAT_ENABLED and isinstance(self.PASSENGER_SEAT_TEMP, int):
            logger.info('Starting passenger seat heater')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=1, level=self.PASSENGER_SEAT_TEMP)
        elif not self.PASSENGER_SEAT_ENABLED or not isinstance(self.PASSENGER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=1, level=0)

        # Rear driver side heater
        if self.REAR_DRIVER_SIDE_SEAT_ENABLED and isinstance(self.REAR_DRIVER_SIDE_SEAT_TEMP, int):
            logger.info('Starting rear driver side seat heater')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=2, level=self.REAR_DRIVER_SIDE_SEAT_TEMP)
        elif not self.REAR_DRIVER_SIDE_SEAT_ENABLED or not isinstance(self.REAR_DRIVER_SIDE_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=2, level=0)

        # There's no #3 heater

        # Rear center heater
        if self.REAR_CENTER_SEAT_ENABLED and isinstance(self.REAR_CENTER_SEAT_TEMP, int):
            logger.info('Starting rear center seat heater')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=4, level=self.REAR_CENTER_SEAT_TEMP)
        elif not self.REAR_CENTER_SEAT_ENABLED or not isinstance(self.REAR_CENTER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=4, level=0)

        # Rear passenger side heater
        if self.REAR_PASSENGER_SIDE_SEAT_ENABLED and isinstance(self.REAR_PASSENGER_SIDE_SEAT_TEMP, int):
            logger.info('Starting rear passenger side seat heater')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=5, level=self.REAR_PASSENGER_SIDE_SEAT_TEMP)
        elif not self.REAR_PASSENGER_SIDE_SEAT_ENABLED or not isinstance(self.REAR_PASSENGER_SIDE_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=5, level=0)

        # Add job to stop the preheating
        end_time = datetime.now(timezone(TZ)) + timedelta(minutes=self.PREHEAT_DURATION)
        logger.info('Scheduling preheating end job at %s', end_time.strftime("%m/%d/%Y, %H:%M:%S"))
        scheduler.add_job(tesla_preheat.stop_preheat, 'date', next_run_time=end_time, id='stop_preheat')

    def stop_preheat(self):
        self.wake_vehicle()

        logger.info('Getting vehicle state...')
        vehicle_data = self.vehicle.get_vehicle_data()
        vehicle_state = vehicle_data['drive_state']['shift_state']
        logger.info('Current vehicle state: %s', vehicle_state if vehicle_state else 'Parked')
        if not vehicle_state:
            logger.info('Stopping preheating...')
            self.vehicle.command('CLIMATE_OFF')
            logger.info('Preheating stopped at %s', datetime.now(timezone(TZ)).strftime("%m/%d/%Y, %H:%M:%S"))
        else:
            logger.info('Preheating won\'t be stopped as vehicle is in function')

        logger.info('Next preheating will occur at %s', scheduler.get_job('start_preheat').next_run_time)

    def wake_vehicle(self):
        logger.info('Waking up vehicle...')
        status = None
        for x in range(1, 10):
            status = self.vehicle.get_vehicle_summary()
            if status['state'] == 'online':
                break
            else:
                self.vehicle.sync_wake_up()
                time.sleep(5)
                continue
        if not status:
            raise VehicleUnavailableException()
        elif status['state'] != 'online':
            raise VehicleUnavailableException()
        logger.info('Vehicle awake and waiting for command')


def convert_to_boolean(value):
    """Return a boolean value translating from other types if necessary.
    """
    if value.lower() not in BOOLEAN_STATES:
        raise ValueError('Not a boolean: %s' % value)
    return BOOLEAN_STATES[value.lower()]


class VehicleUnavailableException(Exception):
    logging.error('Vehicle not available.')


tesla_preheat = TeslaPreHeat()

scheduler = BackgroundScheduler(timezone=TZ)

if tesla_preheat.PREHEAT_DAY_OF_WEEK:
    scheduler.add_job(tesla_preheat.start_preheat, 'cron', day_of_week=tesla_preheat.PREHEAT_DAY_OF_WEEK,
                      hour=tesla_preheat.PREHEAT_HOUR, minute=tesla_preheat.PREHEAT_MINUTE, id='start_preheat')
else:
    scheduler.add_job(tesla_preheat.start_preheat, 'cron', hour=tesla_preheat.PREHEAT_HOUR,
                      minute=tesla_preheat.PREHEAT_MINUTE, id='start_preheat')

scheduler.start()

logger.info('Next preheating will occur at %s', scheduler.get_job('start_preheat').next_run_time)

while True:
    time.sleep(1)
