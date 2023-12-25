#!/bin/bash

# Set the path to your virtual environment
VENV_PATH="/home/ec2-user/starfish_backend/virtualenv"

export CRON_TAB=running
# Activate the virtual environment
source "$VENV_PATH/bin/activate"
cd /home/ec2-user/starfish_backend/djangoBackend/
# Run your Python script (replace script.py with the actual script name)
export DJANGO_SETTINGS_MODULE=djangoBackend.settings
python3 token_updater.py >> logsToken

# Deactivate the virtual environment
deactivate