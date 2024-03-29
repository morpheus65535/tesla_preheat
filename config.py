from configparser import ConfigParser
import os

defaults = {
    'general': {
        'email': 'elon@tesla.com',
        'enabled': False,
        'vehicle_id': '0',
    },
    'heater': {
        'defrost': False,
        'driver_enabled': False,
        'driver_temp': '22',
        'passenger_enabled': False,
        'passenger_temp': '22',
        'heated_steering_wheel': False
    },
    'seat': {
        'front_left_temp': '0',
        'front_right_temp': '0',
        'rear_left_temp': '0',
        'rear_center_temp': '0',
        'rear_right_temp': '0',
    },
    'schedule': {
        'days_of_week': '0,1,2,3,4',
        'start_time': "7:15",
        'duration': '15',
    },
}

settings_file = os.path.join(os.path.dirname(__file__), 'config', 'config.ini')

settings = ConfigParser()
settings.read_dict(defaults)
settings.read(settings_file)


def save_settings(data):
    from tesla import tesla_preheat
    if 'email' in data:
        settings['general']['email'] = str(data['email'])
    else:
        settings['general']['enabled'] = str(data['enabled'])
        settings['general']['vehicle_id'] = str(data['vehicle_id'])
        settings['heater']['defrost'] = str(data['defrost'])
        settings['heater']['driver_enabled'] = str(data['driver_enabled'])
        settings['heater']['driver_temp'] = str(data['driver_temp'])
        settings['heater']['passenger_enabled'] = str(data['passenger_enabled'])
        settings['heater']['passenger_temp'] = str(data['passenger_temp'])
        if tesla_preheat.heated_steering_wheel:
            settings['heater']['heated_steering_wheel'] = str(data['heated_steering_wheel'])
        settings['seat']['front_left_temp'] = data['front_left_temp']
        settings['seat']['front_right_temp'] = data['front_right_temp']
        if tesla_preheat.rear_seat_heaters:
            settings['seat']['rear_left_temp'] = data['rear_left_temp']
            settings['seat']['rear_center_temp'] = data['rear_center_temp']
            settings['seat']['rear_right_temp'] = data['rear_right_temp']
        settings['schedule']['days_of_week'] = data['days_of_week']
        settings['schedule']['start_time'] = data['start_time']
        settings['schedule']['duration'] = data['duration']
    with open(settings_file, 'w') as configfile:
        settings.write(configfile)
