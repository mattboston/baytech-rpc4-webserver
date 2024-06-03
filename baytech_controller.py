#!/usr/bin/python

import serial
import baytech.rpc4serial as rpc4serial
from time import sleep
import json

import threading
import os.path
from pathlib import Path
import logging
import datetime
from random import seed
from random import random

from flask import Flask, jsonify, make_response, request, redirect, url_for, send_from_directory, render_template, send_from_directory
from random import randint

debug = True
log_file = '/opt/baytech_controller/baytech_controller.log'
device='/dev/ttyUSB0'

if debug == True:
    debug_level = logging.DEBUG
else:
    debug_level = logging.INFO
logging.basicConfig(filename=log_file, level=debug_level)
logging.info('%s - Started OfficeStatus app' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') )

app = Flask(__name__)

seed(1)

def main():
    device='/dev/ttyUSB0'
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
    ser = rpc4serial.RPC4_NC(device=device)
    ser.connect()
    ser.state()
    status = ser.getStatus()
    status['tempC'] = float(status['Internal Temperature'].replace(" C",""))
    status['tempF'] = (status['tempC'] * 9/5) + 32
#    logging.info(status)
    ser.close()
    return status

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

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
