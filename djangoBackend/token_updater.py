#!/usr/bin/env python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoBackend.settings")


import django
django.setup()

import sys

from api.models import *
from intuitlib.client import AuthClient
import intuitlib
import pandas as pd
from dateutil.parser import parse
import json
import numpy as np
from django.shortcuts import redirect
import requests
from django.db.models import Q
import base64
from django.http import HttpResponseRedirect
from django.apps import apps
import xmltodict
from django.db import models
from django.contrib import admin
from django.core.management import call_command
import ast
from datetime import datetime, timedelta, date
import time
#CALLBACK_URL = "https://app.usestarfish.com/callback/"
#CLIENT_ID = 'ABanshcAw2qo7vXxsncRXYujqUBdhb9x11xtI1CFZeJXih3Aee'
#SECRET_KEY='ZR2YldS0LkHa43dr09iwvm43LYsjiGOB3So0xWml'
#BASE_URL= "https://quickbooks.api.intuit.com"
CALLBACK_URL = "https://app.usestarfish.com/callback/"
CLIENT_ID = 'ABanshcAw2qo7vXxsncRXYujqUBdhb9x11xtI1CFZeJXih3Aee'
SECRET_KEY='iC544bLWVJISusQG4NH9AL2yg3MXuKViKLgVuErC'
BASE_URL= "https://quickbooks.api.intuit.com"

MODE = 'production'


def generate_access_token(inuit_comp_code, integration_id = ''):
    string_to_encode = CLIENT_ID + ":" + SECRET_KEY
    encoded_string = "Basic " + base64.b64encode(string_to_encode.encode()).decode()
    matching_objects = ''
    if integration_id:
        try:
            matching_objects = IntegrationModel.objects.filter(id=integration_id).values().last()
        except:
            pass

    else:

        try:
            matching_objects = IntegrationModel.objects.filter(Q(inuit_company_id=inuit_comp_code)).values().last()
            
        except IntegrationModel.DoesNotExist:
            # Handle the case where no objects match the conditions
            pass
       
    refresh_token = matching_objects['refresh_token']
    # Define the API endpoint and base URL
    endpoint_path = "/oauth2/v1/tokens/bearer"
    base_url = "https://oauth.platform.intuit.com"  # Replace with your base URL

    # Define headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Authorization": encoded_string
    }

    # Define the form data for the request
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    # Construct the full URL
    url = base_url + endpoint_path

    # Send the POST request with form data
    response = requests.post(url, headers=headers, data=data)

    # Check the response
    if response.status_code == 200:
        # Successful response
        data = response.json()

        if integration_id:
            obj = IntegrationModel.objects.get(id = integration_id)
        else:
            obj = IntegrationModel.objects.filter(Q(inuit_company_id=inuit_comp_code)).last()
        
        obj.access_token = data['access_token']
        obj.refresh_token = data['refresh_token']
        obj.save()
        print(f"Token Updated for {integration_id} : {obj.app_name}")
        
    else:
        print(response.status_code)
    return response.json()

if __name__ == "__main__":
    print(f"{datetime.now()}  : Updating tokens")
    obj = IntegrationModel.objects.all().values()
    for o in obj:
        if o['integration_type']=='online':
            generate_access_token(o['inuit_company_id'], o['id'])
    
    sys.exit()