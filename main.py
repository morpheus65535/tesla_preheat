from waitress import serve
from flask import Flask, render_template, url_for, redirect, request
from datetime import datetime

from config import settings, save_settings
from scheduler_config import scheduler
from tesla import tesla_preheat


app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    authorized = False
    vehicles_list = []
    if tesla_preheat.session.authorized:
        authorized = True
        auth_url = None
        vehicles_list = tesla_preheat.session.vehicle_list()
    else:
        auth_url = tesla_preheat.session.authorization_url()

    next_run_time = 'Disabled or no days selected.'
    if scheduler.bgscheduler.get_job('start_preheat'):
        next_run_time = scheduler.bgscheduler.get_job(job_id='start_preheat').next_run_time
    return render_template('index.html', authorized=authorized, auth_url=auth_url, settings=settings,
                           next_preheat=next_run_time, rear_seat_heaters=tesla_preheat.rear_seat_heaters,
                           heated_steering_wheel=tesla_preheat.heated_steering_wheel, vehicles_list=vehicles_list)


@app.route('/preheat_now', methods=['GET'])
def preheat_now():
    scheduler.bgscheduler.modify_job(job_id='start_preheat', next_run_time=datetime.now())
    scheduler.add_stop_job()
    return redirect(url_for('main'))


@app.route('/save_settings', methods=['POST'])
def save_settings_to_file():
    data = request.get_json()
    save_settings(data)
    tesla_preheat.get_vehicles()
    scheduler.configure()
    return redirect(url_for('main'))


@app.route('/logout', methods=['GET'])
def logout():
    tesla_preheat.session.logout()
    scheduler.configure()
    return redirect(url_for('main'))


@app.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    save_settings(data)
    code_url = data['code_url']
    tesla_preheat.session.fetch_token(authorization_response=code_url)
    scheduler.configure()
    return redirect(url_for('main'))


if __name__ == "__main__":
    serve(app, port=5000)
