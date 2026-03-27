#!/usr/bin/python

import serial
import baytech.rpc4serial as rpc4serial
from time import sleep
import json
import configparser

import threading
import os.path
from pathlib import Path
import logging
import datetime
from random import seed
from random import random

from flask import Flask, jsonify, make_response, request, redirect, url_for, send_from_directory, render_template, send_from_directory
from random import randint
from functools import wraps

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

debug = config.getboolean('baytech', 'debug')
log_file = config.get('baytech', 'log_file')
device = config.get('baytech', 'device')
api_key = config.get('baytech', 'api_key')

if debug:
    debug_level = logging.DEBUG
else:
    debug_level = logging.INFO
logging.basicConfig(filename=log_file, level=debug_level)
logging.info('%s - Started OfficeStatus app' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') )

app = Flask(__name__)

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not key or key != api_key:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

seed(1)

_serial_lock = threading.Lock()

def main():
#    command_prompt=b'>'
#    ser = rpc4serial.RPC4_NC(device=device, command_prompt=command_prompt)
    ser = rpc4serial.RPC4_NC(device=device)
    ser.connect()
    ser.state()
    status = ser.getStatus()
    print(type(status))
    ser.close()
    print('Baytech: %s' % status)
    for key, value in status["outlets"]["8"].items():
        port_8_name = key
        port_8_value = value
    print(port_8_name)
    print(port_8_value)

def getStatus():
    with _serial_lock:
        ser = rpc4serial.RPC4_NC(device=device)
        ser.connect()
        ser.state()
        status = ser.getStatus()
        status['tempC'] = float(status['Internal Temperature'].replace(" C",""))
        status['tempF'] = (status['tempC'] * 9/5) + 32
        ser.close()
    return status

def _extract_single_outlet_name_and_state(outlet_dict):
    """
    rpc4serial returns per-outlet status as a dict with a single key/value pair:
      {"port01": "On"} or {"port01": "Off"}
    """
    if not outlet_dict or not isinstance(outlet_dict, dict):
        return None, None
    for name, state in outlet_dict.items():
        return name, state
    return None, None

def getOutletStatus(port_id):
    """Return a per-port outlet dict like {"port01": "On"}."""
    with _serial_lock:
        ser = rpc4serial.RPC4_NC(device=device)
        ser.connect()
        ser.state()
        outlet_dict = ser.getStatus(port_id)
        ser.close()
    return outlet_dict

def renamePort(port_id, name):
    with _serial_lock:
        ser = rpc4serial.RPC4_NC(device=device)
        ser.connect()
        result = ser.renameOutlet(port_id, name)
        ser.close()
    return result

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/status', methods=["GET"])
@require_api_key
def api_status():
    status = getStatus()
    return jsonify(status)

@app.route('/api/status/<int:port_id>', methods=["GET"])
@require_api_key
def api_status_port(port_id):
    if port_id < 1 or port_id > 8:
        return jsonify({"error": "port_id must be an integer between 1 and 8"}), 400

    outlet_dict = getOutletStatus(port_id)
    name, state = _extract_single_outlet_name_and_state(outlet_dict)
    if state is None:
        return jsonify({"error": f"unable to read status for port_id={port_id}"}), 500

    return jsonify({
        "port_id": port_id,
        "name": name,
        "state": state
    })

@app.route('/api/power/<int:port_id>', methods=["POST"])
@require_api_key
def api_power_port(port_id):
    if port_id < 1 or port_id > 8:
        return jsonify({"error": "port_id must be an integer between 1 and 8"}), 400

    with _serial_lock:
        ser = rpc4serial.RPC4_NC(device=device)
        ser.connect()
        if not ser.state():
            ser.close()
            return jsonify({"error": "not connected to device"}), 500

        # Determine current state
        current_outlet_dict = ser.getStatus(port_id)
        current_name, current_state = _extract_single_outlet_name_and_state(current_outlet_dict)
        if current_state is None:
            ser.close()
            return jsonify({"error": f"unable to read current state for port_id={port_id}"}), 500

        # Toggle
        if current_state == "On":
            ser.turnOff(port_id)
            expected_new_state = "Off"
        else:
            ser.turnOn(port_id)
            expected_new_state = "On"

        # Read back
        new_outlet_dict = ser.getStatus(port_id)
        new_name, new_state = _extract_single_outlet_name_and_state(new_outlet_dict)
        ser.close()

    return jsonify({
        "port_id": port_id,
        "name": new_name if new_name is not None else current_name,
        "previous_state": current_state,
        "new_state": new_state,
        "expected_new_state": expected_new_state
    })

@app.route('/api/port/rename/<int:port_id>', methods=["POST"])
@require_api_key
def api_port_rename(port_id):
    if port_id < 1 or port_id > 8:
        return jsonify({"error": "port_id must be an integer between 1 and 8"}), 400
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "JSON body with 'name' field required"}), 400
    name = data['name'].strip()
    if not name:
        return jsonify({"error": "name cannot be empty"}), 400
    success = renamePort(port_id, name)
    if not success:
        return jsonify({"error": "failed to rename port"}), 500
    return jsonify({"port_id": port_id, "name": name[:10]})

@app.route('/port/rename', methods=["POST"])
def port_rename():
    port_id = int(request.form['port_id'])
    name = request.form['name'].strip()
    if 1 <= port_id <= 8 and name:
        renamePort(port_id, name)
    return redirect("/", code=302)

@app.route('/')
def root():
    status = getStatus()
    return render_template("index.html", status=status)

@app.route('/power', methods=["POST"])
def power():
    if request.method == "POST":
        print(request.form)
        outlet_id = int(request.form['outlet_id'])
        clicked = request.form['clicked']
        print(f"Outlet: { outlet_id }")
        print(f"Clicked: { clicked }")
        with _serial_lock:
            ser = rpc4serial.RPC4_NC(device=device)
            ser.connect()
            if ser.state():
                if clicked == 'On':
                    ser.turnOn(outlet_id)
                else:
                    ser.turnOff(outlet_id)
            ser.close()
    return redirect("/", code=302)

@app.route('/power_all', methods=["POST"])
def power_all():
    if request.method == "POST":
        print(request.form)
        clicked = request.form['clicked']
        print(f"Clicked: { clicked }")
        with _serial_lock:
            ser = rpc4serial.RPC4_NC(device=device)
            ser.connect()
            if ser.state():
                if clicked == 'On':
                    ser.turnOnAll()
                else:
                    ser.turnOffAll()
            ser.close()
    return redirect("/", code=302)


if __name__ == '__main__':
    # main()
    app.run(host='0.0.0.0', debug=debug, port=80)
