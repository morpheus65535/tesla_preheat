import teslapy
import os
from datetime import datetime
import logging
from pytz import utc, timezone

from config import settings
from log_config import logger

TZ = os.getenv('TZ') or utc


class TeslaPreHeat:
    def __init__(self):
        retry = teslapy.Retry(total=5, status_forcelist=(408, 500, 502, 503, 504))
        self.session = teslapy.Tesla(email=settings.get('general', 'email'),
                                     cache_file=os.path.join(os.path.join(os.path.dirname(__file__),
                                                                          'config',
                                                                          'cache.json')),
                                     retry=retry,
                                     timeout=60)
        self.vehicle = None
        self.vehicle_data = None
        self.rear_seat_heaters = False
        self.heated_steering_wheel = False
        self.get_vehicles()

    def get_vehicles(self):
        def _get_vehicle_from_id():
            vehicles_list = self.session.vehicle_list()
            if settings.get('general', 'vehicle_id') == 0:
                return vehicles_list[0]
            else:
                return next((x for x in vehicles_list if x['vehicle_id'] == settings.getint('general', 'vehicle_id')),
                            vehicles_list[0])

        if self.session.authorized:
            try:
                logger.info('Retrieving vehicle...')
                self.vehicle = _get_vehicle_from_id()
                logger.info('Selected vehicle name: %s', self.vehicle['display_name'])
                self.vehicle_data = self.vehicle.get_latest_vehicle_data()
                if 'data' in self.vehicle_data:
                    self.vehicle_data = self.vehicle_data['data']
                if 'vehicle_config' in self.vehicle_data:
                    if 'rear_seat_heaters' in self.vehicle_data['vehicle_config']:
                        self.rear_seat_heaters = False if self.vehicle_data['vehicle_config']['rear_seat_heaters'] == 0\
                            else True
                if 'climate_state' in self.vehicle_data:
                    if 'steering_wheel_heater' in self.vehicle_data['climate_state']:
                        self.heated_steering_wheel = False if \
                            self.vehicle_data['climate_state']['steering_wheel_heater'] is None else True
            except teslapy.HTTPError as e:
                logger.exception(e)

    def start_preheat(self):
        self.get_vehicles()
        try:
            self.wake_vehicle()
        except teslapy.VehicleError as e:
            # unable to wake vehicle
            logger.error(e)
            return
        self.vehicle.command('CLIMATE_ON')

        # Cabin heater
        logger.info('Starting cabin heater...')
        if settings.getboolean('heater', 'driver_enabled'):
            self.vehicle.command('CHANGE_CLIMATE_TEMPERATURE_SETTING',
                                 driver_temp=settings.get('heater', 'driver_temp'))
        if settings.getboolean('heater', 'passenger_enabled'):
            self.vehicle.command('CHANGE_CLIMATE_TEMPERATURE_SETTING',
                                 passenger_temp=settings.get('heater', 'passenger_temp'))
        logger.info('Vehicle cabin heater started')

        # Heated steering wheel
        if settings.getboolean('heater', 'heated_steering_wheel'):
            logger.info('Starting heated steering wheel...')
            self.vehicle.command('REMOTE_STEERING_WHEEL_HEATER_REQUEST', on='true')
            logger.info('Vehicle heated steering wheel started')
        else:
            self.vehicle.command('REMOTE_STEERING_WHEEL_HEATER_REQUEST', on='false')
            logger.info('Vehicle heated steering wheel not requested; skipping')

        # Max defrost
        if settings.getboolean('heater', 'defrost'):
            logger.info('Starting max defrost...')
            self.vehicle.command('MAX_DEFROST', on='true')
            logger.info('Max defrost started')

        # commented out because it turns off heated steering wheel
        # else:
        #    self.vehicle.command('MAX_DEFROST', on='false')
        #    logger.info('Vehicle cabin defrost not requested; skipping.')

        # Driver seat heater
        logger.info('Setting driver seat heater level')
        self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=0,
                             level=settings.getint('seat', 'front_left_temp'))

        # Passenger seat heater
        logger.info('Setting passenger seat heater level')
        self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=1,
                             level=settings.getint('seat', 'front_right_temp'))

        if self.rear_seat_heaters:
            # Rear driver side heater
            logger.info('Setting rear driver side seat heater level')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=2,
                                 level=settings.getint('seat', 'rear_left_temp'))

            # There's no #3 heater

            # Rear center heater
            logger.info('Setting rear center seat heater level')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=4,
                                 level=settings.getint('seat', 'rear_center_temp'))

            # Rear passenger side heater
            logger.info('Setting rear passenger side seat heater Level')
            self.vehicle.command('REMOTE_SEAT_HEATER_REQUEST', heater=5,
                                 level=settings.getint('seat', 'rear_right_temp'))

        # Schedule stop job after specified duration
        from scheduler_config import scheduler
        scheduler.add_stop_job()

    def stop_preheat(self):
        self.get_vehicles()
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

    def wake_vehicle(self):
        logger.info('Waking up vehicle...')
        self.vehicle.sync_wake_up(timeout=300)
        logger.info('Vehicle awake and waiting for command')


class VehicleUnavailableException(Exception):
    if __name__ == "__main__":
        logging.error('Vehicle not available.')


tesla_preheat = TeslaPreHeat()
