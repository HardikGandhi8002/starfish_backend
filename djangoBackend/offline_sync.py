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


def delta_plParent_generator(plparent, integration_id, company_id):
    ### df to be returned
    plparent_delta = pd.DataFrame(columns = plparent.columns)
    plparent_data = PLParent.objects.all().filter(company_id = company_id, integration_id=integration_id).values()
    plparent_df = pd.DataFrame(list(plparent_data))
    
    plparent_df['len'] = [len(x.split('-')) for x in plparent_df['index_ui']]
    plparent['len'] = [len(x.split('-')) for x in plparent['index_ui']]
    temp = plparent_df.merge(plparent, left_on='desc', right_on='desc', how='outer')
    continue_flag = True

    plparent_df.drop(['id'], axis=1, inplace=True)
    plparent_delta['len'] = ''
    ## identify delta
    print(temp[['desc', 'index_ui_x', 'index_ui_y']])
    try:
        headers = temp[pd.isna(temp['index_ui_x'])]
    except:
        ### assumed that the column doesnt exist
        continue_flag = False
    
    if continue_flag:
        print(headers.columns)
        for i, r in headers.iterrows():
            ### find the parent based on index_ui_y
            pa = str(r['index_ui_y']).split('-')[:-1]
            ### create the parent
            t = ''

            for p in pa:
                t+=p + '-'
            parent = t[:-1]

            ### find the parent lines in the main table
            ### lines that start with parent, but not the parent and the level of the nest is the same.
            temp_df = plparent_df[(plparent_df['index_ui'].str.startswith(parent)) & (plparent_df['index_ui']!=parent) & (plparent_df['len']==len(pa)+1)]
            print(temp_df.columns)
            if temp_df.shape[0]>0:
            ### find the last digit of the index_ui
                temp_df['last'] = [x.split('-')[-1] for x in temp_df['index_ui']]
                last_no = max(temp_df['last'].astype(int))
                next_no = last_no +1
                ### recreate the index
                parent = parent + '-' + str(next_no)
                append_list = [ '', '', parent, r['desc'], '', '', '', '', '']
            else:
                append_list = [ '', '', r['index_ui_y'], r['desc'], '', '', '', '', '']
            plparent_df.loc[len(plparent_df)] = append_list
            print(str(len(plparent_df.columns)))
            print(str(len(plparent_delta.columns)))
            print(str(len(append_list)))
            plparent_delta.loc[len(plparent_delta)] = append_list



    plparent_delta.drop(['len'], axis = 1, inplace=True)
    return plparent_delta

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
    print(f"{model} uploaded")
    
def offline(integration_id):
    objs = IntegrationExcelUploadModel.objects.filter(integration_id_id = integration_id, upload_status = True, db_sync=False).values()
    print(objs)
    if objs:
        for obj in objs:
            #### delete records based on the date range
            from_date = obj['from_date']
            to_date = obj['to_date']
            plparent_append_flag = False
            ### define strategy for PL Parent
            if PLParent.objects.filter(company_id=obj['company_id_id'], integration_id = integration_id):
                plparent_append_flag = True
                print('Append mode ON')
            

            try:
                date_col = SegmentColumnMapping.objects.filter(integration_id = integration_id, company_id = obj['company_id_id'], column_name_inuit = 'tx_date').values('column_name_django')[0]['column_name_django']
                query = f"DELETE FROM api_segmentdata as a WHERE a.company_id = CAST({obj['company_id_id']} AS VARCHAR(4)) AND a.integration_id = CAST({integration_id} AS VARCHAR(4)) AND CAST(a.{date_col} AS DATE) BETWEEN '{from_date}' AND '{to_date}';"
                print(query)
                cursor = connection.cursor()
                cursor.execute(query)
                print('Deleted Data')
            except Exception as error:
                print(error)
                pass
            


            file = MEDIA_ROOT + '/'+ obj['transformed_file']
            try:
                data = pd.read_excel(file)
            except:
                print(f"File read error for {obj['transformed_file']}")

            ## Remove unwanted nested columns and creating the PL Table
            data.replace('',float('NaN'))
            plTable = data.iloc[:,0:9].dropna(how="all", axis = 1)
            plTable = plTable.drop_duplicates()
            plTable.reset_index(inplace=True)
            plTable.drop('index', axis = 1, inplace=True)

            plTable.replace(float('NaN'), '')
            index = 1
            column_list = plTable.columns
            for col in plTable.columns:
                if col=='Col1':
                    temp_df = plTable[col]
                    temp_df.drop_duplicates(inplace = True)
                    temp_df.dropna(inplace = True)
                    temp_df = temp_df.reset_index()
                    temp_df.drop('index', axis = 1, inplace = True)
                    temp_df[col + '_index_ui'] = temp_df.index+1
                    plTable = pd.merge(plTable, temp_df, left_on=col, right_on=col, how='left')
                else:
                    col_current = plTable[f'Col{index}'].drop_duplicates()
                    print(col_current)
                    temp_df_ = pd.DataFrame()
                    for col_ in col_current:
                        print(plTable.columns)
                        temp_df = plTable[plTable[f'Col{index}']==col_][col]
                        temp_df.drop_duplicates(inplace = True)
                        temp_df.dropna(inplace = True)
                        temp_df = temp_df.reset_index()
                        temp_df.drop('index', axis = 1, inplace = True)
                        temp_df[col + '_index_ui'] = temp_df.index+1
                        temp_df_ = pd.concat([temp_df_,temp_df], ignore_index=True)


                    plTable = pd.merge(plTable, temp_df_, left_on=col, right_on=col, how='left')

                    index+=1
                

            col_list_table = ['company_id','integration_id','index_ui','desc','account_key','classification','account_type','account_subtype']

            df = pd.DataFrame(columns = col_list_table)
            for i, row in plTable.iterrows():
                temp_index = 1

                for col in column_list:
                    index_ui = ''
                    ## update new df
                    for i in range(temp_index):
                        try:
                            index_ui += str(int(row[f"Col{i+1}_index_ui"])) + '-'
                        except:
                            pass
                    index_ui_ = index_ui[:-1]
                    list_ = ['', '', index_ui_, row[col], '', '', '', '']
                    df.loc[len(df)] = list_
                    temp_index+=1

            df.drop_duplicates('index_ui', inplace = True)
           
            ####regenerate the df as per the append login if flag is true
            if plparent_append_flag:
                df = delta_plParent_generator(plparent = df, company_id = obj['company_id_id'], integration_id = integration_id)

            #### Creating segment Data
            data['count'] = data[column_list].count(1)    
            data['account_key'] = [data.iloc[i]['Col' + str(x['count'])] for i,x in data.iterrows()]
            data = data.iloc[:,10:]
            data = data.replace(float('NaN'), 0)

            ### abs handled in the query
            data['subt_nat_amount'] = data['Credit'] - data['Debit']


            ### populating the account key in the parent table
            account_key_list = np.array(data['account_key'].drop_duplicates())
            for i,r in df.iterrows():
                if r['desc'] in account_key_list:
                    df.at[i, 'account_key'] = r['desc']
                else:
                    df.at[i, 'account_key'] = '-'


            ### REPLACE wherever account key is not present to "-"
            df = df.replace("", "-")

            ## update segment column mapping table##
            segment_mapping_columns = ['column_name_django','column_name_inuit']
            
            data.rename(columns={'Date':'tx_date'}, inplace=True)
            list_title = []
            column_mapping = {}
            mColumns = data.columns
            for c in range(len(mColumns)):
                a= [f'col{c+1}', mColumns[c]]
                list_title.append(a)
            

            column_df = pd.DataFrame(list_title, columns=segment_mapping_columns)
            column_df['column_desc_inuit'] = column_df['column_name_inuit']
            
            data.columns = column_df['column_name_django']
            df.drop(['company_id', 'integration_id'], axis=1, inplace=True)


            #### upload code ##########
            _pandas_to_model('fulldump', data, obj['company_id_id'], integration_id, purge = False)
            _pandas_to_model('column_mapping', column_df, obj['company_id_id'], integration_id, purge = True)
            if df.shape[0]>0:
                _pandas_to_model('plparent', df, obj['company_id_id'], integration_id, purge = False)
            else:
                print('No Delta found in PLParent')

            obj_ = IntegrationExcelUploadModel.objects.get(id = obj['id'])
            obj_.db_sync = True
            obj_.save()

        #### check for location
        integration_df = pd.DataFrame(list(IntegrationModel.objects.filter(id = integration_id).values()))
        company_id= obj['company_id_id']
        if integration_df.iloc[-1]['capture_location']:
            if integration_df.iloc[-1]['location_attr']:
                segment_col = SegmentColumnMapping.objects.filter(company_id = obj['company_id_id'], integration_id = integration_id, column_name_inuit="Department").values("column_name_django").last()['column_name_django']
            else:
                segment_col = SegmentColumnMapping.objects.filter(company_id = obj['company_id_id'], integration_id = integration_id, column_name_inuit="Class").values("column_name_django").last()['column_name_django']



            cursor = connection.cursor()
            query = f" \
            SELECT DISTINCT {segment_col} as description, '{segment_col}' as col_placement, cast('{segment_col}=' as varchar) || cast({segment_col} as varchar) as filter_query, \
            cast({segment_col} as varchar) || cast('({integration_df.iloc[-1]['app_name']})' as varchar) as ui_display\
            FROM api_SegmentData AS A \
            WHERE A.integration_id = cast({integration_id} as varchar) AND A.company_id =cast({company_id} as varchar) \
            AND NOT EXISTS ( \
            SELECT 1 FROM api_locationmodel AS B WHERE cast(B.integration_id as varchar)=A.integration_id AND cast(B.company_id_id as varchar)=A.company_id \
            AND A.{segment_col} = B.description);"

            cursor.execute(query)
            data = dictfetchall(cursor)
            data = pd.DataFrame(data)
            
            _pandas_to_model("locationModel", data, company_id = company_id, integration_id = integration_id, purge = False)
        else:
            loc_obj= LocationModel(company_id = company_id, integration_id = integration_id, description = integration_df.iloc[-1]['app_name'], ui_display = integration_df.iloc[-1]['app_name'])
            loc_obj.save()

        #### updation of the budget model
        cursor = connection.cursor()
        query_budget = QueryModel.objects.filter(query_name = 'insert_budget_model_data').values('query').last()['query']
        try:
            cursor.execute(query_budget.format(obj['company_id_id']))
        except:
            print('error occured in budget model')

        revenue_budget = QueryModel.objects.filter(query_name = 'insert_revenue_budget_model').values('query').last()['query']
        try:
            cursor.execute(revenue_budget.format(obj['company_id_id']))
        except:
            print('error occured in revenue model')


if __name__ == "__main__":
    print(datetime.now())
    obj = IntegrationModel.objects.all().values()
    for o in obj:
        if o['integration_type'] == 'offline':
            offline(o['id'])
