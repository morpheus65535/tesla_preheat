import teslapy
import os
from apscheduler.schedulers.background import BlockingScheduler
from pytz import utc, timezone
from datetime import datetime, timedelta

TZ = os.getenv('TZ') or utc


class TeslaPreHeat:
    def __init__(self):
        self.EMAIL = os.getenv('EMAIL') or None
        self.PASSWORD = os.getenv('PASSWORD') or None

        self.PREHEAT_DAY_OF_WEEK = os.getenv('PREHEAT_DAY_OF_WEEK') or None
        self.PREHEAT_HOUR = int(os.getenv('PREHEAT_HOUR')) or None
        self.PREHEAT_MINUTE = int(os.getenv('PREHEAT_MINUTE')) or None
        self.PREHEAT_DURATION = int(os.getenv('PREHEAT_DURATION')) or None

        self.DRIVER_TEMP = int(os.getenv('DRIVER_TEMP')) if os.getenv('DRIVER_TEMP') else None
        self.PASSENGER_TEMP = int(os.getenv('PASSENGER_TEMP')) if os.getenv('PASSENGER_TEMP') else None
        self.CABIN_PREHEAT_ENABLED = bool(os.getenv('CABIN_PREHEAT_ENABLED')) if os.getenv('CABIN_PREHEAT_ENABLED') \
            else False

        self.DRIVER_SEAT_TEMP = int(os.getenv('DRIVER_SEAT_TEMP')) if os.getenv('DRIVER_SEAT_TEMP') else None
        self.DRIVER_SEAT_ENABLED = bool(os.getenv('DRIVER_SEAT_ENABLED')) if os.getenv('DRIVER_SEAT_ENABLED') else False
        self.PASSENGER_SEAT_TEMP = int(os.getenv('PASSENGER_SEAT_TEMP')) if os.getenv('PASSENGER_SEAT_TEMP') else None
        self.PASSENGER_SEAT_ENABLED = bool(os.getenv('PASSENGER_SEAT_ENABLED')) if os.getenv('PASSENGER_SEAT_ENABLED') \
            else False
        self.REAR_DRIVER_SIDE_SEAT_TEMP = int(os.getenv('REAR_DRIVER_SIDE_SEAT_TEMP')) if \
            os.getenv('REAR_DRIVER_SIDE_SEAT_TEMP') else None
        self.REAR_DRIVER_SIDE_SEAT_ENABLED = bool(os.getenv('REAR_DRIVER_SIDE_SEAT_ENABLED')) if \
            os.getenv('REAR_DRIVER_SIDE_SEAT_ENABLED') else False
        self.REAR_CENTER_SEAT_TEMP = int(os.getenv('REAR_CENTER_SEAT_TEMP')) if os.getenv('REAR_CENTER_SEAT_TEMP') \
            else None
        self.REAR_CENTER_SEAT_ENABLED = bool(os.getenv('REAR_CENTER_SEAT_ENABLED')) if \
            os.getenv('REAR_CENTER_SEAT_ENABLED') else False
        self.REAR_PASSENGER_SIDE_SEAT_TEMP = int(os.getenv('REAR_PASSENGER_SIDE_SEAT_TEMP')) if \
            os.getenv('REAR_PASSENGER_SIDE_SEAT_TEMP') else None
        self.REAR_PASSENGER_SIDE_SEAT_ENABLED = bool(os.getenv('REAR_PASSENGER_SIDE_SEAT_ENABLED')) if \
            os.getenv('REAR_PASSENGER_SIDE_SEAT_ENABLED') else False

        self.CLIENT_ID = 'e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e'
        self.CLIENT_SECRET = 'c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220'

        self.session = teslapy.Tesla(self.EMAIL, self.PASSWORD, self.CLIENT_ID, self.CLIENT_SECRET)
        self.token = self.session.fetch_token()
        
        try:
            self.vehicle = self.session.vehicle_list()[0]
        except teslapy.HTTPError as e:
            print(e)

    def start_preheat(self):
        self.vehicle.sync_wake_up()
    
        # Cabin heater
        if self.CABIN_PREHEAT_ENABLED and self.DRIVER_TEMP and self.PASSENGER_TEMP:
            self.vehicle.command('CHANGE_CLIMATE_TEMPERATURE_SETTING', driver_temp=self.DRIVER_TEMP,
                                 passenger_temp=self.PASSENGER_TEMP)
        self.vehicle.command('CLIMATE_ON')

        # Driver seat heater
        if self.DRIVER_SEAT_ENABLED and isinstance(self.DRIVER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=0, level=self.DRIVER_SEAT_TEMP)
        elif not self.DRIVER_SEAT_ENABLED or not isinstance(self.DRIVER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=0, level=0)

        # Passenger seat heater
        if self.PASSENGER_SEAT_ENABLED and isinstance(self.PASSENGER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=1, level=self.PASSENGER_SEAT_TEMP)
        elif not self.PASSENGER_SEAT_ENABLED or not isinstance(self.PASSENGER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=1, level=0)

        # Rear driver side heater
        if self.REAR_DRIVER_SIDE_SEAT_ENABLED and isinstance(self.REAR_DRIVER_SIDE_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=2, level=self.REAR_DRIVER_SIDE_SEAT_TEMP)
        elif not self.REAR_DRIVER_SIDE_SEAT_ENABLED or not isinstance(self.REAR_DRIVER_SIDE_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=2, level=0)

        # There's no heater=3

        # Rear center heater
        if self.REAR_CENTER_SEAT_ENABLED and isinstance(self.REAR_CENTER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=4, level=self.REAR_CENTER_SEAT_TEMP)
        elif not self.REAR_CENTER_SEAT_ENABLED or not isinstance(self.REAR_CENTER_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=4, level=0)

        # Rear passenger side heater
        if self.REAR_PASSENGER_SIDE_SEAT_ENABLED and isinstance(self.REAR_PASSENGER_SIDE_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=5, level=self.REAR_PASSENGER_SIDE_SEAT_TEMP)
        elif not self.REAR_PASSENGER_SIDE_SEAT_ENABLED or not isinstance(self.REAR_PASSENGER_SIDE_SEAT_TEMP, int):
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=5, level=0)

        # Add job to stop the preheating
        end_time = datetime.now(timezone(TZ)) + timedelta(minutes=self.PREHEAT_DURATION)
        scheduler.add_job(tesla_preheat.stop_preheat, 'date', next_run_time=end_time, id='stop_preheat')

    def stop_preheat(self):
        self.vehicle.sync_wake_up()
        vehicle_data = self.vehicle.get_vehicle_data()
        if 'drive_state' in vehicle_data:
            if 'shift_state' in vehicle_data['drive_state']:
                if not vehicle_data['drive_state']['shift_state']:
                    self.vehicle.command('CLIMATE_OFF')


tesla_preheat = TeslaPreHeat()

scheduler = BlockingScheduler(timezone=TZ)

if tesla_preheat.PREHEAT_DAY_OF_WEEK:
    scheduler.add_job(tesla_preheat.start_preheat, 'cron', day_of_week=tesla_preheat.PREHEAT_DAY_OF_WEEK,
                      hour=tesla_preheat.PREHEAT_HOUR, minute=tesla_preheat.PREHEAT_MINUTE, id='start_preheat')
else:
    scheduler.add_job(tesla_preheat.start_preheat, 'cron', hour=tesla_preheat.PREHEAT_HOUR,
                      minute=tesla_preheat.PREHEAT_MINUTE, id='start_preheat')

scheduler.start()
