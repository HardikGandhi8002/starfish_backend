#!/usr/bin/env python
import django
django.setup()
import os
from api.models import (UserModel, RoleScreenModel, RoleModel, ScreenModel, 
                PriviledgeScreenLocModel, LocationModel, create_model, IntegrationAPIResponseLog, 
                IntegrationModel, IntegrationMappingModel, SegmentData, SegmentColumnMapping, BenchmarkModel, 
                BenchmarkModelOverview, TaskManagerModel, CompanyModel)
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

CALLBACK_URL = "https://app.usestarfish.com/callback/"
CLIENT_ID = 'ABanshcAw2qo7vXxsncRXYujqUBdhb9x11xtI1CFZeJXih3Aee'
SECRET_KEY='ZR2YldS0LkHa43dr09iwvm43LYsjiGOB3So0xWml'
BASE_URL= "https://quickbooks.api.intuit.com"

MODE = 'production'


MAX_FROM_DATE = datetime(2010,1,1)
DELTA_DAYS =120

def _generate_access_token(inuit_comp_code):
    string_to_encode = CLIENT_ID + ":" + SECRET_KEY
    encoded_string = "Basic " + base64.b64encode(string_to_encode.encode()).decode()
    
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
        

    else:
        # Handle errors
        
        auth_client = AuthClient(
            CLIENT_ID,
            SECRET_KEY,
            CALLBACK_URL,
            MODE,
            )
        
        try:
            Scopes = intuitlib.enums.Scopes
            url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
            
            redirect(url)
        except:
            pass
    return response.json()


######### function used to create nested json based on json from the api or directly from merged_df ################
def _json_transformer(report =None, merged_df = None, colDat = None, col_df=None):
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
        for i in item_generator(report['Rows'], "ColData"):
            temp_struct = []
            for j in i:
                temp_struct.append(j['value'])
            colDat.append(temp_struct)
        
        df_temp = pd.DataFrame(colDat)

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
                temp_fd.append(j['value'])
            fulldump.append(temp_fd)
        fulldump = pd.DataFrame(fulldump, columns = colDat)
        
        fulldump['desc'] = ['' if _is_date(x) else x for x in fulldump[colDat[0]]]
        fulldump[colDat[0]] = [x if _is_date(x) else '' for x in fulldump[colDat[0]]]


        parent_dump =[]
        for i in item_generator(report['Rows']['Row'], 'Header'):
            temp_fd = []
            for j in i['ColData']:
                if j['value']!='':
                    temp_fd.append(j['value'])
                try:
                    temp_fd.append(j['id'])
                except:
                    temp_fd.append('')
            parent_dump.append(temp_fd)
        parent_dump = pd.DataFrame(parent_dump)

        parent_dump = parent_dump.replace("", float("NaN")).dropna(how='all', axis=1)
        parent_dump.replace(float("NaN"), '', inplace = True)

        parent_dump.columns =['desc', 'account_key']


        list_test = []
        detail_flag = False
        temp = ''
        for _, row in parent_dump.iterrows():
            if row[1] == '':
                if detail_flag:
                    temp_l = temp.split('-')
                    temp_l = temp_l[:-1]
                    temp_l[-1] = int(temp_l[-1]) + 1
                    temp = ''
                    for i in temp_l:
                        if temp=='':
                            temp=i
                        else:
                            temp+='-'+str(i)
                    detail_flag = False
                    list_test.append(temp)
                else:
                    if len(list_test)>0:
                        temp += '-1'
                        list_test.append(temp)
                    else:
                        temp = '1'
                        list_test.append('1')
            else:

                if detail_flag:
                    temp_l = temp.split('-')
                    temp_l[-1] = int(temp_l[-1]) + 1
                    temp = ''
                    for i in temp_l:
                        if temp=='':
                            temp=i
                        else:
                            temp+='-'+str(i)
                    list_test.append(temp)
                else:
                    if len(list_test)>0:
                        temp += '-1'
                        list_test.append(temp)
                    else:
                        temp = '1'
                        list_test.append('1')
                detail_flag = True
            
            temp = list_test[-1]



        parent_dump['selfId'] = list_test

        merged_df = pd.merge(fulldump, parent_dump, left_on=['desc'], right_on = ['desc'], how='left')


    #### code to convert merges data into nested json starts here ############3
    merged_df.replace(float("NaN"), "", inplace=True)

    id_list = []
    temp_list = []

    for _, row in merged_df.iterrows():
        temp_list.append(row['selfId'])
        if row['selfId']:
            id_list.append(row['selfId'])
        else:
            if temp_list[-2]:
                id_list.append(id_list[-1] + '-1')
            else:
                a = id_list[-1].split('-')
                a[-1] = int(float(a[-1])) + 1
                t = ''
                for _ in a:
                    if t =='':
                        t = _
                    else:
                        t+= '-' + str(_)
                id_list.append(t)

    merged_df['index_ui'] = id_list

    merged_df.drop_duplicates('index_ui', keep='last', inplace=True)
    #### function to create tree structure #########3
    def create_tree_structure(df, parent_key=None):
        result = []

        for index, row in df.iterrows():
            item = {}
            if row['index_ui'].startswith(parent_key + '-') if parent_key else not '-' in row['index_ui']:
                if parent_key is not None:
                    if len(row['index_ui'].split('-')) - len(parent_key.split('-')) <=1:
                        for col in df.columns:
                            item[col] = row[col]
                        children = create_tree_structure(df, row['index_ui'])
                        if children:
                            item['children'] = children

                else:
                    for col in df.columns:
                        item[col] = row[col]
                    children = create_tree_structure(df, row['index_ui'])
                    if children:
                        item['children'] = children
                if item:
                    result.append(item)

        return result

    #### create new index ####
    merged_df['index'] = [x for x in range(len(merged_df))]
    merged_df.set_index('index', inplace = True)
    #### populate the account key at the transaction level ######
    for i in range(len(merged_df)):
        if _is_date(merged_df.iloc[i]['tx_date']):
            merged_df.at[i, 'account_key'] = merged_df.at[i-1,'account_key']

    merged_df.dropna(inplace = True)

    ##### sort as per index_ui ####
    df = merged_df.copy().sort_values('index_ui')

    ##### create main tree structure #####
    tree_structure = create_tree_structure(df, parent_key = '1')

    columns_response = []
    
    #### column data to be sent back #####
    if report is not None:
        colDat.insert(0,'desc')
        colTitle.insert(0,'Description')
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

    return tree_structure, columns_response, merged_df




def _get_pl_detail(inuit_company_id, company_id, integration_id, from_date = MAX_FROM_DATE, from_db = False, plSummary=False, to_date=None):
    json_response = None
    merge_df = None 
    colDat = None
    model = IntegrationModel.objects.filter(Q(inuit_company_id=inuit_company_id)).values().last()

    ### get access token
    response = _generate_access_token(inuit_company_id)
    access_token = response['access_token']

    # authorization 
    auth = "Bearer " + access_token
    base_url = BASE_URL

    endpoint = f"/v3/company/{inuit_company_id}/reports/ProfitAndLossDetail"

    query_params = {
    "start_date": from_date,
    "end_date": datetime.strftime(datetime.now(),"%Y-%m-%d"),
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
        
        

    nested_json, columns_response, merged_df = _json_transformer(json_response)

    
    ##### mapping account details to the fulldump ###########

    account = _get_account_info(inuit_company_id)
    account['account_key'] = account['account_key'].astype(str)
    merged_df = pd.merge(merged_df, account, left_on='account_key', right_on='account_key', how='left')
    
    list_title = []
    mColumns = merged_df.columns
    print(mColumns)
    for c in range(len(mColumns)):
        a= [f'col{c+1}', mColumns[c]]
        list_title.append(a)


    max_col_limit = 30
    extra_col_add = max_col_limit - len(mColumns)

    #########
    ## update segment column mapping table##
    segment_mapping_columns = ['column_name_django','column_name_inuit']
    colTitle = []
    for i in item_generator(json_response['Columns'], 'ColTitle'):
        colTitle.append(i)
    
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

    merged_df = merged_df.replace('', float('NaN'))

    merged_df.dropna(subset=['tx_date'], inplace=True)

    merged_df = merged_df.replace(float('NaN'), '')
    print(merged_df.head(10))

    ### renaming columns #####
    merge_col_list = [f'col{x+1}' for x in range(len(mColumns))]
    merged_df.columns = merge_col_list
    
    ##### adding blank columns ####
    i = 1
    while i+len(mColumns) <= max_col_limit:
        merged_df[f'col{i+len(mColumns)}'] = ''
        i+=1

    ##### adding description to the Column mapping table########
    for index, row in column_df.iterrows():
        try:
            column_df.at[index, 'column_desc_inuit'] = col_mapping[row['column_name_inuit']]
        except:
            column_df.at[index, 'column_desc_inuit'] = ''


    

    _pandas_to_model('fulldump', merged_df, company_id, integration_id)


    ### update merged table #######3
    #s_pandas_to_model('column_mapping', column_df, company_id, integration_id)


    return nested_json,columns_response, merged_df


def _pandas_to_model(model, df, company_id, integration_id, purge = False):
    if model == 'fulldump':
        model_obj = SegmentData
    elif model == 'column_mapping':
        model_obj = SegmentColumnMapping
    else:
        pass

    if purge:
        try:
            model_obj.objects.filter(company_id = company_id, integration_id = integration_id).delete()
            
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


def _get_account_info(inuit_company_id):
    model = IntegrationModel.objects.filter(Q(inuit_company_id=inuit_company_id)).values().last()

    ### get access token
    response = _generate_access_token(inuit_company_id)
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





def main(company_id=None, integration_id=None):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoBackend.settings')

    ##### fetch integration data ###
    integration_data = IntegrationModel.objects.all().values()
    
    ## itter through each integtation data ###
    for integration_data in integration_data:
        date_format_db = "%Y-%m-%d"
        inuit_company_id = integration_data['inuit_company_id']
        integration_id = integration_data['id']
        company_id = integration_data['company_id_id']
        flag = integration_data['max_update']
        to_date = datetime.now().date()
        to_date = datetime.strftime(to_date, date_format_db)

        seg_data = SegmentData.objects.all().filter(company_id = company_id, integration_id = integration_id)

        if flag:
            from_date = datetime.now() - timedelta(DELTA_DAYS)            
        else:
            from_date = MAX_FROM_DATE
            seg_data.delete()

        

        #### filter date as per the dates provided #####
        #### read col data #####
        col_data = SegmentColumnMapping.objects.all().filter(company_id = company_id, integration_id= integration_id).values()
        df = pd.DataFrame(list(col_data))
        print(df)
        try:
            col = np.array(df[df['column_name_inuit']=='tx_date']['column_name_django'])[0]
            print(col)

            
            if seg_data:
                seg_data = seg_data.exclude(**{col:""})
                col = col +"__gte"
                seg_data = seg_data.filter(**{col:from_date})
                seg_data.delete()
            
            from_date = datetime.strftime(from_date, date_format_db)


            _, _, _ =_get_pl_detail(inuit_company_id, company_id=company_id, integration_id=integration_id, from_date=from_date)

            if flag==False:
                print('updating flag')
                integration_obj = IntegrationModel.objects.get(pk = integration_id)
                integration_obj.max_update = True
                integration_obj.save()
        except:
            print('error:'+ str(inuit_company_id) )
        
if __name__ == "__main__":
    main()