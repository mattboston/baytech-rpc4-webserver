#!/bin/bash

# Install the required dependencies
sudo apt-get -y install python3-pip python3-dev python3-venv

# Make sure we're in the proper directory
cd /opt/baytech_controller

# Create a python virtual environment
python3 -m venv .venv

# Activate the python virtual environment
. .venv/bin/activate

# Install the pip modules
pip3 install -r ./requirements.txt

# Install the officestatus systemd service file
sudo cp baytech_controller.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload
