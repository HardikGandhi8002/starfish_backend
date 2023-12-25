#!/usr/bin/env python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoBackend.settings")


import django
django.setup()

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
from djangoBackend.settings import MEDIA_ROOT
from django.db import connection

MODE = "production"
print(f"Running on Mode {MODE}")

if MODE=='sandbox':
    CALLBACK_URL = "http://localhost:3000/callback/"
    CLIENT_ID = 'ABFFEnsqj7pX5P0RzG8QXyVd1dlSKGPTvXVSAJSRiGHAqb8DKm'
    SECRET_KEY='ifJSpxkm5p3RIM8UYD77ACQ5jqaSaWn13WH7reVW'
    BASE_URL= "https://sandbox-quickbooks.api.intuit.com"

if MODE=='production':
    CALLBACK_URL = "https://app.usestarfish.com/callback/"
    CLIENT_ID = 'ABanshcAw2qo7vXxsncRXYujqUBdhb9x11xtI1CFZeJXih3Aee'
    SECRET_KEY='iC544bLWVJISusQG4NH9AL2yg3MXuKViKLgVuErC'
    BASE_URL= "https://quickbooks.api.intuit.com"



MAX_FROM_DATE = datetime(2010,1,1)
DELTA_DAYS =120

def _generate_access_token(integration_id):
    string_to_encode = CLIENT_ID + ":" + SECRET_KEY
    encoded_string = "Basic " + base64.b64encode(string_to_encode.encode()).decode()
    
    try:
        
        matching_objects = IntegrationModel.objects.filter(Q(id=integration_id)).values().last()
        print(f'matching objects found: {matching_objects}')
    except IntegrationModel.DoesNotExist:
        # Handle the case where no objects match the conditions
        pass
        print('no matching objects found')
    refresh_token = matching_objects['refresh_token']
    print(refresh_token)
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

        obj = IntegrationModel.objects.get(id=integration_id)
        obj.access_token = data['access_token']
        obj.refresh_token = data['refresh_token']
        obj.save()
        
    else:
        # Handle errors
        print(f'token response : {response.status_code}')
        auth_client = AuthClient(
            CLIENT_ID,
            SECRET_KEY,
            CALLBACK_URL,
            MODE,
            )
        auth_client.refresh(refresh_token=refresh_token)
        data={}
        data['access_token'] = auth_client.access_token
        obj = IntegrationModel.objects.filter(Q(inuit_company_id=inuit_comp_code))
        obj.access_token = auth_client.access_token
        obj.refresh_token = auth_client.refresh_token
        obj.save()

    return data


######### function used to create nested json based on json from the api or directly from merged_df ################

def _pandas_to_model(model, df, company_id, integration_id, purge = True):
    if model == 'fulldump':
        model_obj = SegmentData
    elif model == 'column_mapping':
        model_obj = SegmentColumnMapping
    elif model == 'plparent':
        model_obj = PLParent
    elif model == 'locationModel':
        model_obj = LocationModel
        
    else:
        pass

    if purge:
        try:
            model_obj.objects.filter(company_id = company_id, integration_id = integration_id).delete()
            model_obj.update()
        except: 
            pass

    # Create a list to store model instances
    instances_to_insert = []
    # additonal columns to be inserted
    # company id and integration id
    df['company_id'] = company_id
    df['integration_id'] = integration_id
    # Iterate through the DataFrame rows and create model instances

    ### Create a bulk Creat instance
    column_df = df.columns
    column_mapping = {}
    for col in column_df:
        column_mapping[col.lower()] = col
    
    
    
    for index, row in df.iterrows():
        instance = model_obj()  # Create an instance of your Django model

        # Populate the instance attributes based on the column_mapping
        for field, column in column_mapping.items():
            
            setattr(instance, field, row[column])

        # Append the instance to the list
        instances_to_insert.append(instance)
    
    
    model_obj.objects.bulk_create(instances_to_insert)
    

from dateutil.parser import parse
def _is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def _get_account_info(integration_id):
    model = IntegrationModel.objects.filter(Q(id=integration_id)).values().last()
    inuit_company_id = model['inuit_company_id']
    ### get access token
    response = _generate_access_token(integration_id)
    access_token = response['access_token']

    # authorization 
    auth = "Bearer " + access_token

    base_url = BASE_URL

    endpoint = f"/v3/company/{inuit_company_id}/query"

    query_params = {
    "query": "select * from Account",
    "minorversion": "69",
    }


    headers={
        "Content-Type": "text/plain", 
        "Authorization":"Bearer " + access_token
    }

    # Combine the base URL, endpoint, and query parameters to create the full URL
    url = f"{base_url}{endpoint}"

    # Send the GET request
    response = requests.get(url, params=query_params, headers= headers)

        # Check the response status code
    if response.status_code == 200:
        # The request was successful, and you can access the response content      
        response = xmltodict.parse(response.text)
        response = json.dumps(response)
        res_df = pd.DataFrame(json.loads(response)['IntuitResponse']['QueryResponse']['Account'])
        res_df['Active'] = [True if x == 'true' else False for x in res_df['Active']]

        for col in res_df.columns:
            if col.startswith('@'):
                res_df.rename(columns = {col:col[1:]}, inplace=True)
        
        res_df.rename(columns = {'Id':'account_key'}, inplace=True)

    else:
        # Handle errors here
        res_df = None
    
    return res_df

def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)


def get_pl_summary(integration_id, from_date, to_date):
    
    print('generate_access_token')
    response = _generate_access_token(integration_id)
    access_token = response['access_token']
    
    inuit_company_id = IntegrationModel.objects.filter(id=integration_id).values('inuit_company_id').last()['inuit_company_id']
    # authorization 
    auth = "Bearer " + access_token
    base_url = BASE_URL
    
    endpoint = f"/v3/company/{inuit_company_id}/reports/ProfitAndLoss"
    
    query_params = {
    "start_date": from_date,
    "end_date": to_date,
    "minorversion": "69",
    }
    
    headers={
        "Content-Type": "text/plain", 
        "Authorization":"Bearer " +access_token
    }
    
    # Combine the base URL, endpoint, and query parameters to create the full URL
    url = f"{base_url}{endpoint}"
    
    response = requests.get(url, params=query_params, headers=headers)
    
    # Check the response status code
    if response.status_code == 200:
        # The request was successful, and you can access the response content as JSON
        json_response = response.json()
        
        
    else:
        # Handle errors here
        pass
        
    with open("sample.json", "w") as outfile:
        json.dump(json_response, outfile)
    
    

    df = _json_transformer_summary(response.json())
    a = df[~(df[0].str.startswith('Total')) & ~((df[1]=='') & ~(df[2]==""))]
    a['index_ui'] = ''
    a.reset_index(inplace=True)

    ### generating the index Ui
    index_list = []
    for i,r in a.iterrows():
        temp = ''
        tt = ''
        tt_ = ''
        ttemp= ''
        print(str(i))
        if r[1] == '':
           ## check if the index_list = []
            if index_list == []:
                ttemp = '1'
            else:
                ### check if the len of the the nest is >1
                temp = index_list[-1]
                if len(temp.split('-')) > 1:
                    ### reduce the nest by 1 and add 1 to it
                    ttemp = ''
                    tt_ = temp.split('-')[:-1]
                    tt__ = tt_[:-1]
                    tt__.append(str(int(tt_[-1])+1))
                    
                    for tt in tt__:
                        tt += '-'
                        ttemp += tt
                        
                        
                    ttemp = ttemp[:-1]
                else:
                    ttemp = str(int(temp)+1)
                    
        else:
            ### check if the previous is outer nest
            if a.iloc[i-1][1] == '':
                ### add a nest
                ttemp = ''
                temp = index_list[-1]
                ttemp = temp + '-1'
            else:
                ## increment the last nest
                temp = index_list[-1]
                tt = temp.split('-')
                tt_ = tt[:-1]
                tt_.append(str(int(tt[-1])+1))
                for t in tt_:
                    t += '-'
                    ttemp += t
                
                ttemp = ttemp[:-1]
                    
        index_list.append(ttemp)    
    a['index_ui'] = index_list
    a.drop([3, 'index'], axis = 1, inplace = True)
    a.rename(columns={0:'desc', 1:'account_key'}, inplace = True)
    a.drop(2, axis= 1, inplace = True)
    #### merging accounts data
    account = _get_account_info(integration_id)
    account = account[['Classification', 'AccountType', 'account_key', 'AccountSubType']]
    merged_df = pd.merge(a, account, left_on='account_key', right_on='account_key', how='left')
    merged_df = merged_df.replace(float('NaN'), '')
    merged_df.rename(columns={'Classification':'classification', 'AccountType':'account_type', 'AccountSubType':'account_subtype'}, inplace=True)
    
    return(merged_df)

def _json_transformer_summary(report =None, merged_df = None, colDat = None, col_df=None):
    def item_generator(json_input, lookup_key):
        if isinstance(json_input, dict):
            for k, v in json_input.items():
                if k == lookup_key:
                    yield v
                else:
                    yield from item_generator(v, lookup_key)
        elif isinstance(json_input, list):
            for item in json_input:
                yield from item_generator(item, lookup_key)
    if report is not None:
        colDat = []
        #for i in item_generator(report['Rows'], "ColData"):
        #    temp_struct = []
        #    for j in i:
        #        temp_struct.append(j['value'])
        #    colDat.append(temp_struct)
        #
        #df_temp = pd.DataFrame(colDat)

        colDat = []
        for i in item_generator(report['Columns'], "Value"):
            temp_struct = []
            colDat.append(i)


        colTitle = []
        for i in item_generator(report['Columns'], "ColTitle"):
            temp_struct = []
            colTitle.append(i)

        fulldump = []
        for i in item_generator(report['Rows']['Row'], 'ColData'):
            temp_fd = []
            for j in i:
                if j['value']!='':
                    temp_fd.append(j['value'])
                try:
                    temp_fd.append(j['id'])
                except:
                    temp_fd.append('')
            fulldump.append(temp_fd)
        fulldump = pd.DataFrame(fulldump)


        fulldump.to_csv('fulldump.csv')

    
    return fulldump

def _get_pl_detail_(integration_id, from_date = '', to_date = '', from_db = False, plSummary=False):
    json_response = None
    merge_df = None 
    colDat = None
    inuit_company_id=IntegrationModel.objects.filter(id = integration_id).values('inuit_company_id').last()['inuit_company_id']

    ### get access token
    print('generate_access_token')
    response = _generate_access_token(integration_id)
    access_token = response['access_token']
    
    # authorization 
    auth = "Bearer " + access_token
    base_url = BASE_URL

    endpoint = f"/v3/company/{inuit_company_id}/reports/ProfitAndLossDetail"

    query_params = {
    "start_date": from_date,
    "end_date": to_date,
    "minorversion": "69",
    }

    headers={
        "Content-Type": "text/plain", 
        "Authorization":"Bearer " +access_token
    }

    # Combine the base URL, endpoint, and query parameters to create the full URL
    url = f"{base_url}{endpoint}"

    response = requests.get(url, params=query_params, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        # The request was successful, and you can access the response content as JSON
        json_response = response.json()
        
        
    else:
        # Handle errors here
        pass
        
    with open("sample.json", "w") as outfile:
        json.dump(json_response, outfile)


   
    nested_json, columns_response, merged_df = _json_transformer_(json_response)

    
    
    ## update segment column mapping table##
    segment_mapping_columns = ['column_name_django','column_name_inuit']
    ####creating Title list
    colTitle = []
    for i in item_generator(json_response['Columns'], 'ColTitle'):
        colTitle.append(i)
    
    colTitle.insert(1, 'Account ID')
    colDat = [i for i in merged_df.columns]
    

    col_mapping = {}
    for cold, colt in zip(colDat, colTitle):
        col_mapping[cold] = colt
    
    list_title = []
    mColumns = merged_df.columns
    for c in range(len(mColumns)):
        a= [f'col{c+1}', mColumns[c]]
        list_title.append(a)

    column_df = pd.DataFrame(list_title, columns=segment_mapping_columns)
    column_df['column_desc_inuit'] = ''

    #merged_df = merged_df.replace('', float('NaN'))

    #merged_df.dropna(subset=['tx_date'], inplace=True)

    merged_df = merged_df.replace(float('NaN'), '')
    #merged_df = merged_df[~(merged_df['tx_date']=='')]
    
    ### renaming columns #####
    merge_col_list = [f'col{x+1}' for x in range(len(mColumns))]
    merged_df.columns = merge_col_list
    
    ##### adding blank columns ####
    i = 1
    max_col_limit =30
    while i+len(mColumns) <= max_col_limit:
        merged_df[f'col{i+len(mColumns)}'] = ''
        i+=1

    ##### adding description to the Column mapping table########
    for index, row in column_df.iterrows():
        try:
            column_df.at[index, 'column_desc_inuit'] = col_mapping[row['column_name_inuit']]
        except:
            column_df.at[index, 'column_desc_inuit'] = ''


    merged_df.to_csv('TempDat.csv')
    column_df.to_csv('Columns.csv')
    #___pandas_to_model('fulldump', merged_df)()


    ### update merged table #######3
    #___pandas_to_model('column_mapping', column_df)()


    return {},column_df, merged_df

def _json_transformer_(report =None, merged_df = None, colDat = None, col_df=None):
    def item_generator(json_input, lookup_key):
        if isinstance(json_input, dict):
            for k, v in json_input.items():
                if k == lookup_key:
                    yield v
                else:
                    yield from item_generator(v, lookup_key)
        elif isinstance(json_input, list):
            for item in json_input:
                yield from item_generator(item, lookup_key)
    if report is not None:
        colDat = []
        #for i in item_generator(report['Rows'], "ColData"):
        #    temp_struct = []
        #    for j in i:
        #        temp_struct.append(j['value'])
        #    colDat.append(temp_struct)
        #
        #df_temp = pd.DataFrame(colDat)

        colDat = []
        for i in item_generator(report['Columns'], "Value"):
            temp_struct = []
            colDat.append(i)


        colTitle = []
        for i in item_generator(report['Columns'], "ColTitle"):
            temp_struct = []
            colTitle.append(i)

        fulldump = []
        try:
            for i in item_generator(report['Rows']['Row'], 'ColData'):
                temp_fd = []
                for j in i:
                    temp_fd.append(j['value'])
                    if len(temp_fd)==1:
                        try:
                            temp_fd.append(j['id'])
                        except:
                            temp_fd.append('')
                fulldump.append(temp_fd)
          
            colDat.insert(1, 'account_key')
            colTitle.insert(1, 'account_key')
            
            fulldump = pd.DataFrame(fulldump, columns = colDat)
            #fulldump = fulldump.replace('',float('NaN'))
            #fulldump.dropna(axis=1, how='all', inplace = True)
            #fulldump = fulldump.replace(float('NaN'),'')
            
        except:
            print('Data not found : ')
            print(report)
            fulldump = pd.DataFrame(columns = colDat)
        
    merged_df = fulldump
    merged_df.replace(float("NaN"), "", inplace=True)

    id_list = []
    temp_list = []
   
      #### create new index ####
    merged_df['index'] = [x for x in range(len(merged_df))]
    merged_df.set_index('index', inplace = True)
    #### populate the account key at the transaction level ######
    try:
        for i in range(len(merged_df)):
            if _is_date(merged_df.iloc[i]['tx_date']):
                merged_df.at[i, 'account_key'] = merged_df.at[i-1,'account_key']
        merged_df.dropna(inplace = True)
        merged_df['flag'] = [_is_date(x) for x in merged_df['tx_date']]
        merged_df = merged_df[merged_df['flag']]
        merged_df.drop('flag', inplace=True, axis = 1)
        
    except:
        print('error occured in updating the tx keys')

        
    ##### sort as per index_ui ####

    ##### create main tree structure #####
   

    columns_response = []
    
    #### column data to be sent back #####
    if report is not None:
        for val, title in zip(colDat, colTitle):
            item_col = {}
            item_col['key'] = val
            item_col['value'] = title
            columns_response.append(item_col)
    else:
        
        colDat = list(col_df['column_name_inuit'])
        colTitle = list(col_df['column_desc_inuit'])

        colDat.insert(0,'desc')
        colTitle.insert(0,'Description')
        for val, title in zip(colDat, colTitle):
            item_col = {}
            item_col['key'] = val
            item_col['value'] = title
            columns_response.append(item_col)

    return {}, columns_response, merged_df




def online(integration_id=None, flag = 'y'):
    ### check if the company id is not null
    if integration_id is not None:
        ### fetch integration details based on the same
        integration_data = IntegrationModel.objects.all().filter(id=integration_id).values()
        integration_df = pd.DataFrame(list(integration_data))
        date_format_db = "%Y-%m-%d"
        inuit_company_id = integration_df.iloc[-1]['inuit_company_id']
        from_date = datetime.now() - timedelta(3650)
        to_date = datetime.now()
        company_id =  pd.DataFrame(list(IntegrationModel.objects.filter(id =integration_id).values())).iloc[-1]['company_id_id']
        
        from_date = datetime.strftime(from_date, date_format_db)
        to_date = datetime.strftime(to_date, date_format_db)
        plSummary = get_pl_summary(integration_id, from_date, to_date)
        print(plSummary)
        
        if PLParent.objects.filter(company_id=company_id, integration_id = integration_id):
            print(f"integration id {integration_id}")
            print(f"company id {company_id}")
        else:
            print('updating parent table')
            _pandas_to_model('plparent', plSummary, company_id, integration_id, purge = True)
        time.sleep(2)
        ### segment data 
        end_date = datetime.now().date()
        if integration_df.iloc[-1]["max_update"] == False:
            start_date = datetime(2013, 1, 1)
            start_date = start_date.date()    
        else:
            start_date = end_date - timedelta(365)
            
            #### purge the data between the given dates in the segment table
            date_col = ''
            try:
                date_col = SegmentColumnMapping.objects.filter(integration_id = integration_id, company_id = company_id, column_name_inuit = 'tx_date').values('column_name_django')[0]['column_name_django']
            except:
                pass
            
            ### run query is there is a 
            if date_col:
                print('Running Query for data purge')
                from_date_ = start_date.strftime("%Y-%m-%d")
                to_date_ = end_date.strftime("%Y-%m-%d")
                query = f"DELETE FROM api_segmentdata as a WHERE a.company_id = CAST({ company_id} AS VARCHAR(4)) AND a.integration_id = CAST({integration_id} AS VARCHAR(4)) AND CAST(a.{date_col} AS DATE) BETWEEN '{from_date_}' AND '{to_date_}';"
                print(query)
                cursor = connection.cursor()
                cursor.execute(query)
        
            
        from_date = start_date
        while from_date <= end_date:
            
            to_date = from_date + timedelta(92)
            
            print(f"fromDate : {from_date}  toDate : {to_date}")
            _,column_df,plTable = _get_pl_detail_(integration_id, from_date =from_date.strftime("%Y-%m-%d"), to_date =to_date.strftime("%Y-%m-%d"), from_db = False, plSummary=False)

            _pandas_to_model('column_mapping', column_df, company_id, integration_id, purge = True)
           
            _pandas_to_model('fulldump', plTable, company_id, integration_id, purge = False)
            from_date = to_date + timedelta(1)
            time.sleep(3)
        
        #### update the max update
        if integration_df.iloc[-1]["max_update"] == False:
            obj_ = IntegrationModel.objects.get(id=integration_id)
            obj_.max_update = True
            obj_.save()

        #### check for location
        if integration_df.iloc[-1]['capture_location']:
            if integration_df.iloc[-1]['location_attr']:
                segment_col = SegmentColumnMapping.objects.filter(company_id = company_id, integration_id = integration_id, column_name_inuit="dept_name").values("column_name_django").last()['column_name_django']
            else:
                segment_col = SegmentColumnMapping.objects.filter(company_id = company_id, integration_id = integration_id, column_name_inuit="klass_name").values("column_name_django").last()['column_name_django']



            cursor = connection.cursor()
            query = f" \
            SELECT DISTINCT {segment_col} as description, '{segment_col}' as col_placement, cast('{segment_col}=' as varchar) || cast({segment_col} as varchar) as filter_query, \
            cast({segment_col} as varchar) || cast('({integration_df.iloc[-1]['app_name']})' as varchar) as ui_display\
            FROM api_SegmentData AS A \
            WHERE A.integration_id = cast({integration_id} as varchar) AND A.company_id =cast({company_id} as varchar) \
            AND NOT EXISTS ( \
            SELECT 1 FROM api_locationmodel AS B WHERE cast(B.integration_id as varchar)=A.integration_id AND cast(B.company_id as varchar)=A.company_id \
            AND A.{segment_col} = B.description);"

            cursor.execute(query)
            data = dictfetchall(cursor)
            data = pd.DataFrame(data)
            
            _pandas_to_model("locationModel", data, company_id = company_id, integration_id = integration_id, purge = False)
        else:
            loc_obj= LocationModel(company_id = company_id, integration_id = integration_id, description = integration_df.iloc[-1]['app_name'], ui_display = integration_df.iloc[-1]['app_name'])
            loc_obj.save()
            

    else:
        print('Invalid Comp / int Id')


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]




if __name__ == "__main__":
    print(datetime.now())
    obj = IntegrationModel.objects.all().values()
    for o in obj:
        if o['integration_type']=='online':
            try:
                online(o['id'])
            except Exception as error:
                # handle the exception
                print(f"An exception occurred:{error} in Integration ID: {o['id']}")