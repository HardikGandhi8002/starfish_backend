from django.shortcuts import render
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
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
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse
from django.apps import apps
import xmltodict
from django.db import models, connection
from django.contrib import admin
from django.core.management import call_command
import ast
from datetime import datetime, timedelta
from django.core.mail import send_mail, EmailMultiAlternatives
import hashlib
import random
from django.contrib.auth.models import PermissionsMixin, User, AbstractUser
from django.conf import settings
import os
from djangoBackend.settings import BASE_DIR, MEDIA_ROOT
import mimetypes

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

LOCATION_TEST = " api_SegmentData.integration_id= cast(13 as varchar) AND col7='Warrens'"

# Create your views here.
########## Fetch Company #####
@api_view(['GET'])
def get_country(request):
    obj = CountryModel.objects.all().values()
    return Response(list(obj))


### code to check if guid exits ####

@api_view(['POST'])
def check_guid(request):
    data = request.POST
    guid = data['code']
   

    response = {}
    objs = RegistrationURLMainModel.objects.all().filter(guid = guid, flag = False).values()

    if len(objs)>0:
        response['verified'] ='pass'
        
        ### change the flag to true
        objs = RegistrationURLMainModel.objects.get(guid = guid)
        objs.token_used_flag=True
        objs.flag=True
        objs.save()
        response['companyName'] = objs.company_name
        response['companyEmail'] = objs.email
        
    else:
        response['verified']='expired'


    return Response(response)

#### code to save guid and trigger mail. ######

@api_view(['POST'])
def trigger_mail(request):
    data = request.POST
    email = data['email']
    company_name = data['company_name']

    #### generate guid #### 
    guid = hashlib.sha1(str(random.random()).encode('utf-8')).hexdigest()

    objs = RegistrationURLMainModel(
        email = email,
        company_name=company_name,
        guid = guid,
        token_used_flag=False
    )

    objs.save()

    #### code to trigger mail.
    response = {}
    text_content = 'This is an important message.'
    message = f"<html><body><p>Thank you for registering to usestarfish.com. In order to complete your registration, can you please proceed click on this <a href = 'https://app.usestarfish.com/register/?code={guid}'> Link</a></p><p>Regards </p>            <p>Team Starfish</p></body></html>"
    try:
        subject = "Verify your email address"
        html_content = message
        from_email = settings.EMAIL_HOST_USER
        to_email = [email]
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        response['status'] = 'Please check your email to complete the registration.'
    except:
        response['status'] = "Error in sending mail"
        response['guid'] = guid

    return Response(response)

@api_view(['POST'])
def reg_data(request):
    _res_dict = {}
    #try:
    data = request.POST
   
    company_fields = [
        'companyName',
        'companyPhone',
        'companyAddr1',
        'companyAddr2',
        'companyCountry',
        'companyEmail',
        'companyCity',
        'companyZipCode',
        'companyState',
    ]
    obj = CompanyModel(
        name = data['companyName'],
        email_id=data['companyEmail'],
        address_1=data['companyAddr1'],
        address_2=data['companyAddr2'],
        country_name=data['companyCountry'],
        state_name=data['companyState'],
        city=data['companyCity'],
        zip_code=data['companyZipCode'],
        phone_number=data['companyPhone'],
        active=True,
        registration_ip_address = get_client_ip(request),
        activation_ip_address = get_client_ip(request)
    )
    obj.save()

    ### get company ID
    company_id = obj.company_id

    ### create user data
    if User.objects.filter(username=data['companyEmail']):
        _res_dict={'registration_status':'This Email id is already registered.'}
    else:
        user=User.objects.create_user(data['companyEmail'], password=data['pass'])
        #user_id = user.id
        
        ### update the custom User model
        try:
            userModel = UserModel(
                user_id = User.objects.get(username=data['companyEmail']),
                company_id_id = company_id,
                first_name = data['firstName'],
                last_name = data['lastName'],
                email_id = data['userEmail'],
                address_1 = data['userAddr1'],
                address_2 = data['userAddr2'],
                state_name = data['userState'],
                city = data['userCity'],
                phone_number=data['userPhone'],
                active = True,
                registration_ip_address = get_client_ip(request),
                activation_ip_address = get_client_ip(request),
                token=data['code'],
                role_id_id = 1,
                country_name = data['userCountry']

            )
            userModel.save()
            _res_dict={'registration_status':'passed'}
        except:
            _res_dict={'registration_status':'Error'}

       

    return Response(_res_dict)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def test(request):
    return Response({request.user.id})


########### code to get users ###########3

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_users(request):
    user_id = request.user.id
    user_data = UserModel.objects.filter(user_id = user_id).values()[0]
    company_id = user_data['company_id_id']

    ### get entire list of users in a company ###########
    comp_user_data = UserModel.objects.all().filter(company_id_id=company_id, active = True).values()
    comp_user_df = pd.DataFrame(list(comp_user_data))
    
    relevant_info = ['user_id_id', 'first_name', 'last_name', 'email_id']
    user_list = []
    try:
        for _, rows in comp_user_df.iterrows():
            temp={}
            for label in relevant_info:
                temp[label] = rows[label]

            user_list.append(temp)
    except:
        pass
        
    res_dict = {}
    res_dict['data'] = user_list
    return Response(res_dict)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_task(request):
    data = request.POST
    user_id = request.user.id
    user_data = UserModel.objects.filter(user_id = user_id).values()[0]
    company_id = user_data['company_id_id']
    if data['taskId']:
        ##### update task data ###########
        if data['action']=='modify':
            try:
                obj_to_update = TaskManagerModel.objects.get(pk=data['taskId'])  # Replace '1' with the primary key of the object you want to update
                obj_to_update.task_title = data['task_title']
                obj_to_update.task_desc = data['task_desc']
                #obj_to_update.created_by = UserModel(user_id_id=request.user.id),
                #assigned_to = UserModel.objects.get(user_id_id=data['assigned_to']),
                obj_to_update.status = data['status']
                obj_to_update.save()
                task_id = data['taskId']
            except TaskManagerModel.DoesNotExist:
                # Handle the case where the object with the given ID does not exist
                pass
        elif data['action'] =='delete':
            TaskManagerModel.objects.all().filter(pk=data['taskId'], created_by_id=UserModel(user_id_id=request.user.id)).delete()
        elif data['action'] =='status_update':
            obj_to_update  = TaskManagerModel.objects.get(pk=data['taskId'])  # Replace '1' with the primary key of the object you want to update
            obj_to_update.status = data['status']
            obj_to_update.save()

    else:
        #######Create new task ###########
        new_entry = TaskManagerModel.objects.create(
            task_title = data['task_title'],
            task_desc = data['task_desc'],
            created_by = UserModel.objects.get(user_id_id=request.user.id),
            assigned_to = UserModel.objects.get(user_id_id=data['assigned_to']),
            status = data['status'],
            company_id_id = company_id,
            due_on = data['due_on']
        )
        new_entry.save()
        task_id = (TaskManagerModel.objects.last()).id
    temp_dict = {}
    try:
        temp_dict['data'] = task_id
    except:
        temp_dict['data'] = ''
    return Response(temp_dict)

################# Pull Task Data ##############3

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_tasks(request):
    data = request.POST
    user_id = request.user.id
    user_data = UserModel.objects.filter(user_id = user_id).values()[0]
    company_id = user_data['company_id_id']
    response = None
    flag = False
    if data['type'] == 'created':
        #### fetch data as per the assigned to user
        model_data = TaskManagerModel.objects.all().filter(created_by_id=UserModel(user_id_id=request.user.id)).values()
        flag = True
    elif data['type'] == 'assigned':
        #### filter data as per the created by user
        model_data = TaskManagerModel.objects.all().filter(assigned_to_id=UserModel(user_id_id=request.user.id)).values()
        flag = True
    else:
        flag = False
    
    if flag:
        df = pd.DataFrame(list(model_data))
       
        df = df[(df['status']=='Not yet Started') | (df['status']=='In Progress')]
        
        name_data = UserModel.objects.all().filter(company_id_id=company_id).values()
        name_df = pd.DataFrame(list(name_data))
        name_df = name_df[['user_id_id','first_name', 'last_name']]

        if data['type']=='assigned':
            user = 'created_by_id'
        else:
            user = 'assigned_to_id'
        response = []
        if df.shape[0]:
            final_df = pd.merge(df, name_df, left_on=user, right_on='user_id_id', how='left')
            final_df =final_df.replace(float('NaN'), '')
            
            for _, row in final_df.iterrows():
                temp = {}
                for col in final_df.columns:
                    temp[col] = row[col]
                
                response.append(temp)

    
    res_dict = {}
    res_dict['data'] = response
    return Response(res_dict)

######## Code to fetch budget ##########
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_budget(request):

    params = generate_params(request)
    try:
        response = fetch_data_from_db('fetch_budget_query', params)
    except:
        response = pd.DataFrame(columns=['desc', 'subt_nat_amount_x', 'subt_nat_amount_y'])
    print(response)
    try:
        target_revenue = fetch_data_from_db('fetch_revenue_target_query', params)
    except:
        target_revenue = ''
    try: 
        achieved_revenue = fetch_data_from_db('fetch_revenue_achieved_query', params)
    except:
        achieved_revenue = ''
    try:
        target_expense = fetch_data_from_db('fetch_budget_target_query', params)
    except:
        target_expense = ''
    try:
        achieved_expense = fetch_data_from_db('fetch_budget_achieved_query', params)
    except:
        achieved_expense = ''
    
    response.set_index('desc', inplace = True)
    
   
    budget_dict = {}

    #target_revenue.at[0,'target_revenue'] = 0 if float(achieved_revenue.loc[0, :].item())-float(target_revenue.loc[0,:].item()) <0 else float(achieved_revenue.loc[0, :].item())-float(target_revenue.loc[0,:].item())
    #target_expense.at[0,'target_expense'] = 0 if float(achieved_expense.loc[0, :].item())-float(target_expense.loc[0,:].item()) <0 else float(achieved_expense.loc[0, :].item())-float(target_expense.loc[0,:].item())
    budget_dict['target_revenue'] = target_revenue
    budget_dict['achieved_revenue'] = achieved_revenue
    budget_dict['target_expense'] = target_expense
    budget_dict['achieved_expense'] = achieved_expense
    budget_dict['categories'] = list(response.index)
    budget_dict['series'] = ['Total', 'Target']
    budget_dict['value'] = ''
    budget_dict['data'] = [{'total':[response['subt_nat_amount_x']], 'target':[response['budget_amount']]}]
    
    #except:
    #    budget_dict = {}
    #    budget_dict['target_revenue'] = {'budget_revenue':[]}
    #    budget_dict['achieved_revenue'] = {'actual_revenue':[]}
    #    budget_dict['target_expense'] = {'budget_expense':[]}
    #    budget_dict['achieved_expense'] = {'actual_expense':[]}
    #    budget_dict['categories'] = []
    #    budget_dict['series'] = ['Total', 'Target']
    #    budget_dict['value'] = ''
    #    budget_dict['data'] = [{'total':0, 'target':0}]

    return Response(budget_dict)

######### Code to get Screens ###############


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_screens(request):
    # get user name from jwt
    user_id = request.user.id
    user_data = UserModel.objects.all().filter(user_id = user_id).values()[0]
    role_id = user_data['role_id_id']
   
    ## Check Role is active or not.
    role_data = RoleModel.objects.filter(role_id = role_id).values()[0]
    response_data = {}
    response_data['status'] = 301
    if role_data['active']:
        role_screen_data = RoleScreenModel.objects.all().filter(role_id_id = role_id).values()
        #screen_data = ScreenModel.objects.all().values()
        screen_list = []
        screen = {}
        for rsd in role_screen_data:
            if ScreenModel.objects.filter(screen_id=rsd['screen_id_id']).values()[0]['active']:
                screen['id'] = rsd['screen_id_id']
                screen['name'] = ScreenModel.objects.filter(screen_id=rsd['screen_id_id']).values()[0]['description'] 
                screen['data_control'] = ScreenModel.objects.filter(screen_id=rsd['screen_id_id']).values()[0]['data_control'] 
                screen_list += [screen]
                screen ={}

        response_data['status'] = 200
        response_data['screen_list'] = screen_list

    return Response(response_data)
    
##### Code to fetch authorised locations #########33

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_locations(request):
    response_data = get_locations(request)

    return Response(response_data)

############ Code to fetch integration keys ##################

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fetch_integration_keys(request):
    ## fetch user Id
    user_id = request.user.id
    int_data = IntegrationModel.objects.filter(Q(user_id=user_id)).values().last()

    response = {}
    response['client_id'] = CLIENT_ID
    response['secret_key'] = SECRET_KEY
    response['inuit_company_id'] = int_data['inuit_company_id']

    return Response(response)


################# Generate the Redirect Url ###################


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_url(request):
    data = request.POST
    user_id = request.user.id
    userData = UserModel.objects.filter(user_id = user_id).values()[0]

    ## companyID
    company_id = userData['company_id_id']
    url=''
    ### check if the id is passed
    reset_token_flag = True 
    integration_id=''
    try:
        integration_id = data['integration_id']
    except:
        reset_token_flag = False

    if integration_id and reset_token_flag:
        integration_data = IntegrationModel.objects.filter(id=integration_id).values()[0]
        try:
            data = generate_access_token(integration_data['inuit_company_id'], str(integration_id))
            print(data)
            if 'error' in data.keys():
                url = ''
                print(data)
            else:
                url='/Dash'
        except:
            print('failed here!.')

    if url=='':
        auth_client = AuthClient(
            client_id=CLIENT_ID,
            client_secret=SECRET_KEY,
            environment=MODE,
            redirect_uri=CALLBACK_URL,
        )
        
        
        Scopes = intuitlib.enums.Scopes
        url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
   
  
    return Response(url)

### To fetch PL Detail From the log/Table

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_plDetail(request):
    
    nested_json,columns_response, merged_df = get_pl_detail_new(request)
    data_plTable = {}
    data_plTable['columns'] = columns_response
    data_plTable['data'] = nested_json
    merged_df = merged_df.replace(float('NaN'), 0)
    merged_df = merged_df.drop('index_ui', axis=1)
    merged_df.drop([ 'classification', 'account_key'], axis= 1, inplace=True)
    data_plTable['table'] = merged_df.values.tolist()

    return Response(data_plTable)

#### to fetch transaction based on the account_key

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_transactions(request):
    data = request.POST
    params = generate_params(request)
    print(params)
    account_key = data['accountKey']
    ## companyID
   
    # fetch column mapping
    ## change columns name
    column_mapping_data = SegmentColumnMapping.objects.all().filter(company_id=params['company_id'], integration_id = params['integration_id']).values()
    df = pd.DataFrame(list(column_mapping_data))
    params['account_key'] = account_key
    segmentData = fetch_data_from_db('fetch_transactions_query', params)
    segment_data = segmentData.replace(float('NaN'), '')
    rename_col={}
    for index, row in df.iterrows():
        rename_col[row['column_name_django']] = row['column_name_inuit']

    col_to_drop = []
    for col in segmentData.columns:
        if col not in rename_col.keys():
            col_to_drop.append(col)
    
    segmentData.rename(columns = rename_col, inplace=True)
    segmentData.drop(col_to_drop, axis=1, inplace=True)
    
    segmentData.replace("", float("NaN"), inplace = True)
    segmentData.dropna(how='all', axis = 1, inplace = True)

    ### creating colDat
    df.replace('',float('NaN'), inplace=True)
    df.dropna(inplace=True)


 
   
    columns = []
    for col in segmentData.columns:
        temp = {}
        temp['key'] = col
        temp['value'] = np.array(df[df['column_name_inuit']==col]['column_desc_inuit'])
        if len(temp['value'])>0:
            temp['value'] = temp['value'][0]
            columns.append(temp)
    
    segmentData = segmentData.replace(float("NaN"), "")
    response = []
    for index, row in segmentData.iterrows():
        temp = {}
        for col in segmentData.columns:
            temp[col] = row[col]
        response.append(temp)

   
    res_dict = {}
    res_dict['data'] = response
    res_dict['columns'] = columns

    return Response(res_dict)



##### to handle the call back
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth(request):
    data = request.POST
    auth_code = request.POST['code']
    comp_id = request.POST['realmId']
    userData = UserModel.objects.filter(user_id = request.user.id).values()[0]
    integration_id = data['integration_id']
    ## companyID
    company_id = userData['company_id_id']
    print(data)

    auth_client = AuthClient(
        client_id=CLIENT_ID,
        client_secret=SECRET_KEY,
        environment=MODE,
        redirect_uri=CALLBACK_URL,
    )

    obj = IntegrationModel.objects.get(pk = int(integration_id))
    obj.inuit_company_id = comp_id
    if obj.refresh_token == '' or obj.refresh_token is None:
        auth_client.get_bearer_token(auth_code, realm_id=comp_id)
        access_token = auth_client.access_token
        refresh_token = auth_client.refresh_token
        obj.access_token = access_token
        obj.refresh_token = refresh_token
        obj.save()
        print("Updated Tokens")

    return Response('/Dash')
        


########### Overview from the costs sheet ########################

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_overview(request):
    #basing it on the classification
    ## fetch the accounts table
    data = request.POST
    user_id = request.user.id
    userData = UserModel.objects.filter(user_id = user_id).values()[0]

    ## companyID
    company_id = userData['company_id_id']
    integration_id = IntegrationModel.objects.filter(company_id_id = company_id).last().id
    

    # fetch column mapping
    column_mapping_data = SegmentColumnMapping.objects.all().values()
    df = pd.DataFrame(list(column_mapping_data))
    
    df = df[(df['company_id']==str(company_id)) & (df['integration_id']==str(integration_id))]

    #fetch full dump
    segment_data = SegmentData.objects.all().filter(company_id=company_id).values()
    segmentData = pd.DataFrame(list(segment_data))

    segmentData = segmentData[(segmentData['company_id']==str(company_id)) & (segmentData['integration_id']==str(integration_id))]
    
    
    rename_col={}
    for index, row in df.iterrows():
        rename_col[row['column_name_django']] = row['column_name_inuit']

    col_to_drop = []
    for col in segmentData.columns:
        if col not in rename_col.keys():
            col_to_drop.append(col)
    
    segmentData.rename(columns = rename_col, inplace=True)
    segmentData.drop(col_to_drop, axis=1, inplace=True)
    
    segmentData.replace("", float("NaN"), inplace = True)
    segmentData.dropna(how='all', axis = 1, inplace = True)
    segmentData = segmentData[~segmentData['account_key'].isna()]
    segmentData = segmentData[~segmentData['tx_date'].isna()]
    
    convert = True
    try:
        from_date = data['fromDate']
        to_date = data['toDate']
        
    except:
        from_date = datetime.now() - timedelta(365)
        to_date = datetime.now()
        convert = False

    if convert:
        incoming_date_format = "%m-%d-%Y"
        from_date = datetime.strptime(from_date, incoming_date_format)
        to_date = datetime.strptime(to_date, incoming_date_format)


    date_format_data = "%Y-%m-%d"
    segmentData['tx_date'] = pd.to_datetime(segmentData['tx_date'], format = date_format_data)
    
    ### pull data within date range
    segmentData = segmentData[(segmentData['tx_date']>=from_date) & (segmentData['tx_date']<=to_date)]
    
    ####converting to float
    segmentData['subt_nat_amount'] = segmentData['subt_nat_amount'].astype(float).round(2)
    
    #### code to add the plparent 
    plparent=PLParent.objects.all().filter(company_id = str(company_id)).values()

    plparent_df = pd.DataFrame(list(plparent))

    segmentData = pd.merge(segmentData,plparent_df, left_on='account_key', right_on='account_key', how='left')
  


    subtotalClassification = segmentData[['subt_nat_amount', 'classification']].groupby('classification').sum()
    
    
    subtotal_by_name = segmentData[['desc', 'subt_nat_amount', 'classification']].groupby(['classification','desc']).sum()
    

    segmentData['month'] = segmentData['tx_date'].dt.month
   
    subtotalClassificationMonth = segmentData[['subt_nat_amount', 'classification','month']].groupby(['classification','month']).sum()

    subtotalNameMonth = segmentData[['subt_nat_amount', 'desc','classification', 'month']].groupby(['desc','month']).sum()
   

    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']

    try:
        revenue_df = subtotalClassificationMonth.loc['Revenue']
        revenue_categories = [month_list[x-1] for x in list(revenue_df.index)]
        revenue_data = revenue_df['subt_nat_amount'].astype(float).round(2)
        revenue_dict={}
        revenue_dict['categories'] = revenue_categories
        revenue_dict['series'] = 'Revenue'
        revenue_dict['value'] = round(subtotalClassification.loc['Revenue']['subt_nat_amount'],2)
        revenue_dict['data'] = revenue_data
    except:
        revenue_dict = {}
        revenue_dict['value'] = 0
        revenue_df = pd.DataFrame(columns = subtotalClassificationMonth.columns)
        revenue_df['month'] = ''
        revenue_df.set_index('month', inplace = True)
        revenue_categories = []
    

    
    try:
        expense_df = subtotalClassificationMonth.loc['Expense']
        
        expense_categories = [month_list[x-1] for x in list(expense_df.index)]
        expense_data = expense_df['subt_nat_amount'].round(2)

        expense_dict={}
        expense_dict['categories'] = expense_categories
        expense_dict['series'] = 'Expense'
        expense_dict['value'] = round(subtotalClassification.loc['Expense']['subt_nat_amount'], 2)
        expense_dict['data'] = expense_data
    except:
        expense_dict = {}
        expense_dict['value'] = 0
        expense_df = pd.DataFrame(columns = subtotalClassificationMonth.columns)
        expense_df['month'] = ''
        expense_df.set_index('month', inplace = True)
        expense_categories = []

    try:
        income_df = pd.merge(revenue_df, expense_df, left_on=revenue_df.index, right_on=expense_df.index, how='outer')
        income_df = income_df.replace(float('NaN'), 0)
        income_df['income'] = income_df['subt_nat_amount_x'] - income_df['subt_nat_amount_y']
        if len(expense_categories) >= len(revenue_categories):
            income_categories = expense_categories  
        else:
            income_categories = revenue_categories
        income_data = income_df['income'].round(2)
        income_dict={}
        income_dict['categories'] = income_categories
        income_dict['series'] = 'Income'
        
        if revenue_df.shape[0]>0:
            revenue_tot = subtotalClassification.loc['Revenue']['subt_nat_amount']
        else:
            revenue_tot = 0

        if expense_df.shape[0]>0:
            expense_tot = subtotalClassification.loc['Expense']['subt_nat_amount']
        else:
            expense_tot = 0
        
        income_dict['value'] = round( revenue_tot - expense_tot,2)
        income_dict['data'] = income_data
        
    except:
        income_dict = {}
        income_dict['value'] = 0

    try:
        subtotalName = segmentData[['subt_nat_amount', 'classification', 'desc', 'month']].groupby(['desc']).sum()
        subtotalNameMonth = segmentData[['subt_nat_amount', 'classification', 'desc', 'month']].groupby(['desc', 'month']).sum()
        
        
        cogs_df = subtotalNameMonth.loc['Cost of Goods Sold']
        cogs_categories = [month_list[x-1] for x in list(cogs_df.index)]
        cogs_data = cogs_df['subt_nat_amount'].round(2)

        cogs_dict={}
        cogs_dict['categories'] = cogs_categories
        cogs_dict['series'] = 'COGS'
        cogs_dict['value'] = subtotalName['subt_nat_amount']
        cogs_dict['data'] = cogs_data
    except:
        
        cogs_dict={}
        cogs_dict['value'] = 0
    

    try:
        budget_dict = {}
        df = subtotal_by_name.copy()
        df = df.reset_index(level = [1])

        budget_dict['categories'] = df.loc['Expense']['desc']
        budget_dict['series'] = ['Total', 'Target']
        budget_dict['value'] = ''
        budget_dict['data'] = [{'total':[df.loc['Expense']['subt_nat_amount']], 'target':[]}]
        
    except:
        budget_dict = {}
    
    wins_dict = {}
    
    #wins_df = segmentData[['subt_nat_amount', 'desc','classification', 'month']].groupby(['Classification','desc','month']).sum()
    #wins_df =wins_df.reset_index(level = [0,1,2])
    #wins_df = wins_df.sort_values('month')
    #wins_df = wins_df[wins_df['Classification']=='Expense']
    #wins_df = wins_df.sort_values(['desc','month'], ascending = False)
    
    
    #current_wins_df = wins_df[wins_df['month']==wins_df['month'].max()]
    #previous_wins_df = wins_df[wins_df['month']==wins_df['month'].max()-1]
    #combined_wins_df = pd.merge(current_wins_df,previous_wins_df, left_on='desc', right_on='desc', how='inner')
    #combined_wins_df['change'] = round(combined_wins_df['subt_nat_amount_x'] - combined_wins_df['subt_nat_amount_y'],2) 
    #combined_wins_df['per_change'] = round(100*(combined_wins_df['subt_nat_amount_x'] - combined_wins_df['subt_nat_amount_y'])/combined_wins_df['subt_nat_amount_y'],2)
    #wins = combined_wins_df.sort_values(['per_change'], ascending=False)
    #losses = combined_wins_df.sort_values(['per_change'], ascending=True)

    current_df = segmentData
    current_df = current_df[['subt_nat_amount', 'desc']].groupby(['desc']).sum()
   
   

    ## Changing the from and to date to the previous year
    from_date = from_date-timedelta(365)
    to_date = to_date-timedelta(365)
    ##### Regenerating the segment Data
    segment_data = SegmentData.objects.all().filter(company_id=company_id).values()
    segmentData = pd.DataFrame(list(segment_data))

    segmentData = segmentData[(segmentData['company_id']==str(company_id)) & (segmentData['integration_id']==str(integration_id))]
    
    segmentData.rename(columns = rename_col, inplace=True)
    segmentData.drop(col_to_drop, axis=1, inplace=True)
    
    segmentData.replace("", float("NaN"), inplace = True)
    segmentData.dropna(how='all', axis = 1, inplace = True)
    segmentData = segmentData[~segmentData['account_key'].isna()]
    segmentData = segmentData[~segmentData['tx_date'].isna()]
    

    date_format_data = "%Y-%m-%d"
    segmentData['tx_date'] = pd.to_datetime(segmentData['tx_date'], format = date_format_data)
    
    #### updating the classification in the segment data
    segmentData = pd.merge(segmentData,plparent_df, left_on='account_key', right_on='account_key', how='left')



    previous_df = segmentData[(segmentData['tx_date']>=from_date) &(segmentData['tx_date']<=to_date)]
    previous_df['subt_nat_amount'] = previous_df['subt_nat_amount'].astype(float).round(2)
   
    previous_df = previous_df[['subt_nat_amount', 'desc']].groupby(['desc']).sum()

    combined_wins_df = pd.merge(current_df,previous_df, left_on=current_df.index, right_on=previous_df.index, how='outer')
    combined_wins_df = combined_wins_df.replace(float('NaN'), 0)

    combined_wins_df['change'] = round(combined_wins_df['subt_nat_amount_x'] - combined_wins_df['subt_nat_amount_y'],2) 
    combined_wins_df['per_change'] = round(100*(combined_wins_df['subt_nat_amount_x'] - combined_wins_df['subt_nat_amount_y'])/combined_wins_df['subt_nat_amount_y'].astype(float).round(2),2)
    combined_wins_df = combined_wins_df.replace(float('inf'), 100)
    combined_wins_df = combined_wins_df.replace(float('-inf'), -100)
    combined_wins_df.reset_index(inplace = True)
    combined_wins_df.rename(columns = {'key_0':'desc'}, inplace=True)
    
    

    wins = combined_wins_df.sort_values(['per_change'], ascending=True)
    losses = combined_wins_df.sort_values(['per_change'], ascending=False)
    wins_list = []
    wins = wins[(wins['per_change'].astype(float).round(2)<0)]
    losses = losses[(losses['per_change'].astype(float).round(2)>0)]
    
    for index,rows in wins.iterrows():
        temp = {}
        temp['name'] = rows['desc']
        temp['change'] = rows['change']
        temp['per_change'] = rows['per_change']
        wins_list.append(temp)

    losses_list = []
   

    for index,rows in losses.iterrows():
        temp = {}
        temp['name'] = rows['desc']
        temp['change'] = rows['change']
        temp['per_change'] = rows['per_change']
        losses_list.append(temp)


    win_loss_data = {}
    win_loss_data['wins'] = wins_list
    win_loss_data['losses'] = losses_list

    response_dict  = {}
    response_dict['revenue'] = revenue_dict
    response_dict['expense'] = expense_dict
    response_dict['income'] = income_dict
    response_dict['cogs'] = cogs_dict
    response_dict['budget_bar'] = budget_dict
    response_dict['wlData'] = win_loss_data
    
    

    return Response(response_dict)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_overview_new(request):
    params = generate_params(request)
    #### subtotalClassificationMonth ###########
    try:
        subtotalClassificationMonth = fetch_data_from_db('subtotal_classification_month', params)

        #### Subtotalclassification #####
        subtotalClassification = fetch_data_from_db('subtotal_classification', params)

        
        subtotalClassification['subt_nat_amount'] = subtotalClassification['subt_nat_amount'].astype(float)
        subtotalClassificationMonth['subt_nat_amount'] = subtotalClassificationMonth['subt_nat_amount'].astype(float)
    except:
        subtotalClassification = pd.DataFrame(columns=['classification', 'subt_nat_amount'])
        subtotalClassificationMonth = pd.DataFrame(columns=['classification', 'subt_nat_amount', 'month'])
        

    try:
        revenue_df = subtotalClassificationMonth[subtotalClassificationMonth['classification']=='Revenue']
        revenue_categories = revenue_df['ui_label']
        revenue_data = revenue_df['subt_nat_amount'].round(2)
        revenue_dict={}
        revenue_dict['categories'] = revenue_categories
        revenue_dict['series'] = 'Revenue'
        revenue_dict['value'] = round(subtotalClassification[subtotalClassification['classification']=='Revenue']['subt_nat_amount'],2)
        revenue_dict['data'] = revenue_data
        revenue_df.set_index('ui_label', inplace = True)

    except:
        revenue_dict = {}
        revenue_dict['value'] = 0
        revenue_df = pd.DataFrame(columns = ['ui_label', 'classification', 'subt_nat_amount'])
        #revenue_df['ui_label'] = ''
        revenue_df.set_index('ui_label', inplace = True)
        revenue_categories = []
    
  


    print(revenue_df)
    try:
        expense_df = subtotalClassificationMonth[subtotalClassificationMonth['classification']=='Expense']
        expense_categories = list(expense_df['ui_label'])
        expense_data = expense_df['subt_nat_amount'].round(2)
        expense_df.set_index('ui_label', inplace = True)
        expense_dict={}
        expense_dict['categories'] = expense_categories
        expense_dict['series'] = 'Expense'
        expense_dict['value'] = round(subtotalClassification[subtotalClassification['classification']=='Expense']['subt_nat_amount'], 2)
        expense_dict['data'] = expense_data
    except:
        expense_dict = {}
        expense_dict['value'] = 0
        expense_df = pd.DataFrame(columns = ['ui_label', 'classification', 'subt_nat_amount'])
        expense_df.set_index('ui_label', inplace = True)
        expense_categories = []

    print(expense_df)

    try:
        income_df = pd.merge(revenue_df, expense_df, left_on=revenue_df.index, right_on=expense_df.index, how='outer')
        print(income_df)
        income_df = income_df.replace(float('NaN'), 0)
        income_df['income'] = income_df['subt_nat_amount_x'] - income_df['subt_nat_amount_y']
        income_df = income_df.replace(float('NaN'), 0)
    except:
        income_df = pd.DataFrame()       

    try:    
        income_data = income_df['income'].round(2)
        income_dict={}
        income_dict['categories'] = income_df['key_0']
        income_dict['series'] = 'Income'
        if revenue_df.shape[0]>0:
            revenue_tot = subtotalClassification[subtotalClassification['classification']=='Revenue']['subt_nat_amount'].item()
        else:
            revenue_tot = 0

        if expense_df.shape[0]>0:
            expense_tot = subtotalClassification[subtotalClassification['classification']=='Expense']['subt_nat_amount'].item()
        else:
            expense_tot = 0
        
        income_dict['value'] =round( revenue_tot - expense_tot,2)
        income_dict['data'] = income_data
        print(income_dict)        
    except:
        income_dict = {}
        income_dict['value'] = 0

    
    

   
    wins_dict = {}
    wins_list = []
    
    
    try:
        combined_wins_df = fetch_data_from_db('wins_loses_query', params)
        combined_wins_df['subt_nat_amount_x'] = combined_wins_df['subt_nat_amount_x'].astype(float)
        combined_wins_df['subt_nat_amount_y'] = combined_wins_df['subt_nat_amount_y'].astype(float)

        combined_wins_df['change'] = round(combined_wins_df['subt_nat_amount_x'] - combined_wins_df['subt_nat_amount_y'],2) 
        combined_wins_df['per_change'] = round(100*(combined_wins_df['subt_nat_amount_x'] - combined_wins_df['subt_nat_amount_y'])/combined_wins_df['subt_nat_amount_y'].astype(float).round(2),2)
        combined_wins_df = combined_wins_df.replace(float('inf'), 100)
        combined_wins_df = combined_wins_df.replace(float('-inf'), -100)
        
        wins = combined_wins_df.sort_values(['per_change'], ascending=True)
        losses = combined_wins_df.sort_values(['per_change'], ascending=False)
        wins = wins[(wins['per_change'].astype(float).round(2)<0)]
        losses = losses[(losses['per_change'].astype(float).round(2)>0)]
    except:
       wins = pd.DataFrame(columns = ['desc', 'change', 'per_change'])
       losses = pd.DataFrame(columns = ['desc', 'change', 'per_change'])


    for index,rows in wins.iterrows():
        temp = {}
        temp['name'] = rows['desc']
        temp['change'] = rows['change']
        temp['per_change'] = rows['per_change']
        wins_list.append(temp)

    losses_list = []
   

    for index,rows in losses.iterrows():
        temp = {}
        temp['name'] = rows['desc']
        temp['change'] = rows['change']
        temp['per_change'] = rows['per_change']
        losses_list.append(temp)


    win_loss_data = {}
    win_loss_data['wins'] = wins_list
    win_loss_data['losses'] = losses_list


    response_dict  = {}
    response_dict['revenue'] = revenue_dict
    response_dict['expense'] = expense_dict
    response_dict['income'] = income_dict

    response_dict['wlData'] = win_loss_data
    
    

    return Response(response_dict)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_benchmark(request):
     #basing it on the classification
    ## fetch the accounts table
    data = request.POST
    user_id = request.user.id
    userData = UserModel.objects.filter(user_id = user_id).values()[0]

    ## companyID
    company_id = userData['company_id_id']
    integration_id = IntegrationModel.objects.filter(company_id_id = company_id).last().id
    

    # fetch column mapping
    column_mapping_data = SegmentColumnMapping.objects.all().values()
    df = pd.DataFrame(list(column_mapping_data))
    
    df = df[(df['company_id']==str(company_id)) & (df['integration_id']==str(integration_id))]

    #fetch full dump
    segment_data = SegmentData.objects.all().values()
    segmentData = pd.DataFrame(list(segment_data))

    segmentData = segmentData[(segmentData['company_id']==str(company_id)) & (segmentData['integration_id']==str(integration_id))]
 
    
    rename_col={}
    for index, row in df.iterrows():
        rename_col[row['column_name_django']] = row['column_name_inuit']

    col_to_drop = []
    for col in segmentData.columns:
        if col not in rename_col.keys():
            col_to_drop.append(col)
    
    segmentData.rename(columns = rename_col, inplace=True)
    segmentData.drop(col_to_drop, axis=1, inplace=True)
    
    segmentData.replace("", float("NaN"), inplace = True)
    segmentData.dropna(how='all', axis = 1, inplace = True)
    segmentData = segmentData[~segmentData['account_key'].isna()]
    segmentData = segmentData[~segmentData['tx_date'].isna()]

    convert = True
    try:
        from_date = data['fromDate']
        to_date = data['toDate']
    except:
        from_date = datetime.now() - timedelta(365)
        to_date = datetime.now()
        convert = False


    if convert:
        incoming_date_format = "%m-%d-%Y"
        from_date = datetime.strptime(from_date, incoming_date_format)
        to_date = datetime.strptime(to_date, incoming_date_format)



    date_format_data = "%Y-%m-%d"
    segmentData['tx_date'] = pd.to_datetime(segmentData['tx_date'], format = date_format_data)

    ### pull data within date range
    segmentData = segmentData[(segmentData['tx_date']>=from_date) & (segmentData['tx_date']<=to_date)]

    ####converting to float
    segmentData['subt_nat_amount'] = segmentData['subt_nat_amount'].astype(float).round(2)
    #### code to insert parent table
    plparent=PLParent.objects.all().filter(company_id = company_id).values()
    plparent_df = pd.DataFrame(plparent)
    segmentData = pd.merge(segmentData,plparent_df, left_on='account_key', right_on='account_key', how='left')


    subtotalClassification = segmentData[['subt_nat_amount', 'classification']].groupby(['classification']).sum()
    
    try:
        revenue = float(subtotalClassification.loc['Revenue'])
    except:
        revenue = 0.0

    try:
        expense = float(subtotalClassification.loc['Expense'])
    except:
        expense = 0.0

    try:
        exp_rev = round(float(100*expense/revenue),2) 
    except:
        exp_rev = 100

    try:
        inc_rev = round(float(100*(revenue-expense)/revenue),2)
    except:
        inc_rev = -100


    bmo_model = BenchmarkModelOverview.objects.all().values()
    if bmo_model:
        bmo_df = pd.DataFrame(list(bmo_model))
        
        bmo_df = bmo_df[(bmo_df['company_id'] == str(company_id)) & (bmo_df['integration_id'] == str(integration_id))]
        benchmark_dict = {}

        try:
            benchmark_dict['exp_rev'] = exp_rev 
            benchmark_dict['inc_rev'] = inc_rev
            benchmark_dict['avg_cost'] = bmo_df.iloc[-1]['avg_cost'] 
            benchmark_dict['avg_inc'] = bmo_df.iloc[-1]['avg_inc']
            benchmark_dict['bic_cost'] = bmo_df.iloc[-1]['bic_cost']
            benchmark_dict['bic_inc'] = bmo_df.iloc[-1]['bic_inc']

        except:
            pass
    else:
        benchmark_dict = {}
        benchmark_dict['exp_rev'] = exp_rev
        benchmark_dict['inc_rev'] = inc_rev
        benchmark_dict['avg_cost'] = 0
        benchmark_dict['avg_inc'] = 0
        benchmark_dict['bic_cost'] = 0
        benchmark_dict['bic_inc'] = 0
    

    

    subtotalClassificationName = segmentData[['subt_nat_amount', 'classification','desc']].groupby(['classification', 'desc']).sum()

    #import benchmark model
    benchmark_model = BenchmarkModel.objects.all().values()
    benchmark_response = {}

    

    if benchmark_model:
        benchmark_df = pd.DataFrame(list(benchmark_model))
        benchmark_df = benchmark_df[(benchmark_df['company_id']==str(company_id)) & (benchmark_df['integration_id']==str(integration_id))]
    else:
        benchmark_df = pd.DataFrame(columns=['expense_head', 'best_in_class', 'avg_in_class'])
    ### identify the maintained benchmarks
    expense_df = subtotalClassificationName.loc['Expense']

    expense_df = expense_df.reset_index(level=[0])
    combined = pd.merge(expense_df, benchmark_df, left_on='desc', right_on='expense_head', how='left')
    combined  = combined.replace(float('NaN'), '-')
    benchmark_table = []
    for _, row in combined.iterrows():
        temp = {}
        temp['expense_head'] = row['desc']
        temp['best_in_class'] = row['best_in_class']
        temp['avg_in_class'] = row['avg_in_class']
        temp['metric'] = round(float(100*row['subt_nat_amount']/expense),2)
        benchmark_table.append(temp)
        
    benchmark_response['table'] = benchmark_table



    benchmark_response['overview'] = benchmark_dict
    
    return Response(benchmark_response)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fetch_benchmark_new(request):
    params = generate_params(request)
    #### subtotalClassificationMonth ###########
    try:
        subtotalClassificationMonth = fetch_data_from_db('subtotal_classification_month', params)
    

        #### Subtotalclassification #####
        subtotalClassification = fetch_data_from_db('subtotal_classification', params)

        ###
        
        subtotalClassification['subt_nat_amount'] = subtotalClassification['subt_nat_amount'].astype(float)
        subtotalClassificationMonth['subt_nat_amount'] = subtotalClassificationMonth['subt_nat_amount'].astype(float)
    except:
        pass


    #### add the expense total to the params #######
    try:
        params['expense_total'] = subtotalClassification[subtotalClassification['classification']=='Expense']['subt_nat_amount'].item()
    except:
        pass
    try:
        revenue = float(subtotalClassification[subtotalClassification['classification']=='Revenue']['subt_nat_amount'].item())
    except:
        revenue = 0.0

    try:
        expense = float(subtotalClassification[subtotalClassification['classification']=='Expense']['subt_nat_amount'].item())
    except:
        expense = 0.0
    print(f"revenue: {revenue}")
    print(f"expense: {expense}")

    try:
        exp_rev = round(float(100*expense/revenue),2) 
    except:
        exp_rev = 100

    try:
        inc_rev = round(float(100*(revenue-expense)/revenue),2)
    except:
        inc_rev = -100


    try:
        bmo_model = BenchmarkModelOverview.objects.all().filter(company_id = params['company_id'], integration_id=params['integration_id']).values()
    except:
        bmo_model = None
    if bmo_model:
        bmo_df = pd.DataFrame(list(bmo_model))
        print(bmo_df)
        
        try:
            benchmark_dict = {}
            benchmark_dict['exp_rev'] = exp_rev 
            benchmark_dict['inc_rev'] = inc_rev
            benchmark_dict['avg_cost'] = bmo_df.iloc[-1]['avg_cost'] 
            benchmark_dict['avg_inc'] = bmo_df.iloc[-1]['avg_inc']
            benchmark_dict['bic_cost'] = bmo_df.iloc[-1]['bic_cost']
            benchmark_dict['bic_inc'] = bmo_df.iloc[-1]['bic_inc']
            
        except:
            pass
    else:
        benchmark_dict = {}
        benchmark_dict['exp_rev'] = exp_rev
        benchmark_dict['inc_rev'] = inc_rev
        benchmark_dict['avg_cost'] = 0
        benchmark_dict['avg_inc'] = 0
        benchmark_dict['bic_cost'] = 0
        benchmark_dict['bic_inc'] = 0
    
    print(benchmark_dict)
    benchmark_table = []

    try:
        combined = fetch_data_from_db('fetch_benchmark_query', params)
        combined  = combined.replace(float('NaN'), '-')
        print(combined.columns)
        for _, row in combined.iterrows():
            temp = {}
            temp['expense_head'] = row['desc']
            temp['best_in_class'] = row['best_in_class']
            temp['avg_in_class'] = row['avg_in_class']
            temp['metric'] = row['your_business']
            benchmark_table.append(temp)
    except:
        pass        

    benchmark_response = {}
    benchmark_response['table'] = benchmark_table
    benchmark_response['overview'] = benchmark_dict

    return Response(benchmark_response)





######### function to handle settings ############
@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def roles_auth_handler_edit(request):
    ## get the user id and other details
    user_id = request.user.id
    data = request.POST
    userData = UserModel.objects.filter(user_id = user_id).values()[0]
    ## companyID
    company_id = userData['company_id_id']
    if request.method =='POST':
        

        

        ### check for the type of change
        ### the possible type of changes are Priviledge / Add user /  integration
        allowed_types = ['priviledge', 'user', 'integration']
        request_type = data['type']
        action = data['action']
        model_id = data['model_id']
        model_data = data['model_data']
        model_data['company_id_id'] = company_id
        if model_id is None:
            model_id = ''


        def model_modification(request_type, model_id = '', data = {}):
            if request_type == 'priviledge':
                model = PriviledgeModel()
            elif request_type == 'user':
                model = UserModel()
            elif request_type == 'integration':
                model = IntegrationModel()

            if model_id !='':
                model = model.__class__.object.get(id = model_id)
                
            for k, v in data.items():
                setattr(model, k, v)
            model.save()

        model_modification(request_type, model_id, model_data)


    #### func for response gen
    def response_gen(model, comp_id, columns = '*'):
        query = f"SELECT {columns} FROM API_{model} AS A WHERE A.COMPANY_ID_ID={comp_id}"
        cursor = connection.cursor()
        cursor.execute(query)
        response = dictfetchall(cursor)
        cursor.close()
        connection.close()
        return response
            
    ### preparing response
    ### repsonse for priviledge
    
   
    priv_response = response_gen("PriviledgeModel", company_id)
    integration_response = response_gen("IntegrationModel", company_id, 
        "id, date_updated, inuit_company_id, app_name, integration_type, capture_location, location_attr")
    user_response = response_gen("UserModel", company_id)

    response = {}
    response['integration'] = integration_response
    response['priv'] = priv_response
    #response['user'] = user_response


    return Response(response)


@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def save_integration(request):
    ## get the user id and other details
    user_id = request.user.id
    data = request.POST
    userData = UserModel.objects.filter(user_id = user_id).values()[0]
    ## companyID
    company_id = userData['company_id_id']
    if request.method =='POST':
        obj = IntegrationModel(app_name = data['app_name'], integration_type=data['integration_type'], user_id = UserModel.objects.get(pk = user_id),
        client_id = CLIENT_ID, secret_key=SECRET_KEY, capture_location=True if data['capture_location']=='true' else False, location_attr = True if data['location_attr']=='true' else False, company_id = CompanyModel.objects.get(pk = company_id))
        obj.save()
    #### func for response gen
    def response_gen(model, comp_id, columns = '*'):
        query = f"SELECT {columns} FROM API_{model} AS A WHERE A.COMPANY_ID_ID={comp_id}"
        cursor = connection.cursor()
        cursor.execute(query)
        response = dictfetchall(cursor)
        connection.close()
        cursor.close()
        return response

    ### preparing response
    ### repsonse for priviledge
    
   
    
    integration_response = response_gen("IntegrationModel", company_id, 
    "id, date_updated, inuit_company_id, app_name, integration_type, capture_location, location_attr")
    
    response = {}
    response['integration'] = integration_response
    
    return Response(response)

#
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fetch_excel_data(request):
    query = QueryModel.objects.filter(query_name='fetch_excels_uploaded').values('query').last()['query']
    cursor = connection.cursor()
    cursor.execute(query)
    return Response(dictfetchall(cursor))

@api_view(["GET", "POST"])
def file_upload_test(request):
    if request.method == 'POST':
        print(request.FILES)
        a = FileModel(user_file = request.FILES['file'])
        a.save()
        return Response("Done")
    else:
        return Response("failed")

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def file_upload_user(request):
    if request.method == 'POST':
        data = request.POST
        user_id = request.user.id
        userData = UserModel.objects.filter(user_id = user_id).values()[0]

        try:
            user_type = data['user_type']
        except:
            user_type = ''
        
        if user_type=='puser':
            obj = IntegrationExcelUploadModel.objects.get(id = data['id'])
            obj.transformed_file = request.FILES['file']
            obj.upload_status = True
            obj.save()

        else:
            incoming_date_format = "%m-%d-%Y"
            from_date = data['from_date']
            from_date = datetime.strptime(from_date, incoming_date_format)

            to_date = data['to_date']
            to_date = datetime.strptime(to_date, incoming_date_format)

            from_date = from_date.strftime("%Y-%m-%d")
            to_date = to_date.strftime("%Y-%m-%d")

            ## companyID
            company_id = userData['company_id_id']
            obj = IntegrationExcelUploadModel(integration_id_id = data['integration_id'],
            company_id = CompanyModel.objects.get(company_id = company_id), from_date = from_date, to_date = to_date, user_file = request.FILES['file'])
            obj.save() 
            
        return Response("Done")
    else:
        return Response("failed")


@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def fetch_budget_settings(request):
    ## generate params
    params = generate_params(request)
    ## add classification to it

    params['classification'] = request.POST['type']
    columns = ['desc']

    if params['classification'] == 'Expense':
        budget_df = fetch_data_from_db('fetch_budget_settings_query', params)

    elif params['classification'] == 'Revenue':
        budget_df = fetch_data_from_db('fetch_revenue_budget_year_data', params)
        budget_df['desc'] = 'Revenue Head'
        budget_df['classification'] = 'Revenue'
        ## Setting up the sequence of columns
        budget_df = budget_df[['desc', 'classification', 'amount', 'year', 'company_id_id', 'buget_id_id']]
    else:
        print("No data found")
        budget_df = pd.DataFrame(columns = ['desc', 'classification', 'amount', 'year', 'company_id_Id', 'buget_id_id'])


    current_year = str(datetime.now().year)
    prev_year = str(datetime.now().year - 1)
    next_year = str(datetime.now().year + 1)
    later_year = str(datetime.now().year + 2)
    year_list = [prev_year, current_year, next_year, later_year]

    # added to year list
    columns += year_list
    #try:
    budget_df.drop_duplicates(subset = ['desc', 'year'], keep='last', inplace=True)
    unique_desc = budget_df.copy()
    df = pd.DataFrame(columns = ['id', 'desc']+year_list)

    response_list = []
    for i, ud in unique_desc.iterrows():
        df.loc[len(df)] = [ud['buget_id_id'], ud['desc'], unique_desc[(unique_desc['desc'] == ud['desc']) & (unique_desc['year'] == int(prev_year))]['amount'].sum(),
                        unique_desc[(unique_desc['desc'] == ud['desc']) & (unique_desc['year'] == int(current_year))]['amount'].sum(),
                        unique_desc[(unique_desc['desc'] == ud['desc']) & (unique_desc['year'] == int(next_year))]['amount'].sum(),
                        unique_desc[(unique_desc['desc'] == ud['desc']) & (unique_desc['year'] == int(later_year))]['amount'].sum()
                        ]
        
    df.drop_duplicates(subset= ['id', 'desc'], inplace = True)
    for i, r in df.iterrows():
        temp_dict = {}
        temp_dict['id'] = r['id']
        temp_dict['desc'] = r['desc']
        temp_dict[prev_year] = r[prev_year]
        temp_dict[current_year] = r[current_year]
        temp_dict[next_year] = r[next_year]
        temp_dict[later_year] = r[later_year]
    
        response_list.append(temp_dict)

    return Response([response_list])
    #except:
    #    return Response([{"status": "Error"}])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_budget_settings(request):
    years = request.POST['year'].split(',')
    print(years)
    budget_id = request.POST['budgetId']
    amount = request.POST['amount'].split(',')
    response = {}

    ### fetch obj 
    try:
        if request.POST['classification'] == 'Expense':
            for yr,amt in zip(years, amount):
                obj = BudgetByYearModel.objects.filter(buget_id_id=budget_id, year = yr).last()
                print(obj)
                if obj is not None:
                    obj.amount = amt
                    
                else:
                    obj = BudgetByYearModel(buget_id_id=budget_id, year = yr, amount = amt)

                obj.save()
        elif request.POST['classification'] == 'Revenue':
            for yr,amt in zip(years, amount):
                obj = RevenueByYearModel.objects.filter(buget_id_id=budget_id, year = yr).last()
                print(obj)
                if obj is not None:
                    obj.amount = amt
                    
                else:
                    obj = RevenueByYearModel(buget_id_id=budget_id, year = yr, amount = amt)

                obj.save()
        response['status'] = 'update successfull'
    except Exception as error:
        print(f"Exception occured in updating budget {error}")
        response['status'] = 'failed in updating'
    return Response(response)



def file_download(request, id):
    int_id = id
    data = IntegrationExcelUploadModel.objects.filter(id = int_id).values()

    media_path = '/home/ec2-user/starfish_backend/djangoBackend/media/'+data[0]['user_file']
    fl = open(media_path, 'r')
    mime_type, _ = mimetypes.guess_type(media_path)
    with open(media_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename={}'.format(data[0]['user_file'].split('/')[1])
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_auth_data(request):
    user_id = request.user.id
    userData = UserModel.objects.filter(user_id = user_id).values()[0]

    ## companyID
    company_id = userData['company_id_id']
    query_dict = dict(company_id = company_id)
    ### 
    role_query = QueryModel.objects.filter(query_name = 'fetch_roles').values('query').last()['query']
    priv_query=  QueryModel.objects.filter(query_name = 'fetch_priviledges_based_on_compid').values('query').last()['query'].format(**query_dict)

    cursor = connection.cursor()
    response_dict = {}
    cursor.execute(role_query)
    response_dict['roles'] = dictfetchall(cursor)
    cursor.execute(priv_query)
    response_dict['priviledges'] = dictfetchall(cursor)

    user_query= QueryModel.objects.filter(query_name = 'fetch_user_auth_obj_compid').values('query').last()['query'].format(**query_dict)
    cursor=connection.cursor()
    cursor.execute(user_query)
    user_data = dictfetchall(cursor)
    response_dict['users'] = user_data
    connection.close()
    return Response(response_dict)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_user(request):
    data = request.POST
    user_id = request.user.id
    userData = UserModel.objects.filter(user_id = user_id).values()[0]
    
    ## companyID
    company_id = userData['company_id_id']

    ### create user
    _res_dict = {}
    flag = True
    try:
        user=User.objects.create_user(data['userEmail'], password=data['pass'])
    except:
        _res_dict['registration_status'] = "User already exists."
        flag=False
    # update other data
    try:
        if flag:
            userModel = UserModel(
            user_id = User.objects.get(username=data['userEmail']),
            company_id_id = company_id,
            first_name = data['firstName'],
            last_name = data['lastName'],
            email_id = data['userEmail'],
            active = True,
            registration_ip_address = get_client_ip(request),
            activation_ip_address = get_client_ip(request),
            role_id_id = data['role_id'],
            priviledge_id_id = data['priviledge_id'],

        )
            userModel.save()
            _res_dict['registration_status']='passed'
        
    except:
        _res_dict['registration_status']='error'


    return Response(_res_dict)
#
#
#
#
#
#
##################### UTILITY FUNCTIONS ###############################
#


def generate_params(request):
    #basing it on the classification
    ## fetch the accounts table
    cursor = connection.cursor()
    data = request.POST
    user_id = request.user.id
    userData = UserModel.objects.filter(user_id = user_id).values()[0]

    ## companyID
    company_id = userData['company_id_id']
    
    ### creating a list of valid locations 
    response = get_locations(request)
    location_df = pd.DataFrame(response)
    location_filter_query = ''
    if 'ui_label' in location_df.columns:
        try:
            location_filter = location_df[location_df['ui_label']==data['location']]['ddl_value'].item()
            print(location_filter)
        except:
            location_filter = location_df.iloc[0]['ddl_value']
        try:
            location_filter_query = location_filter.split('|')[0]
        except:
            location_filter = "''|''"
    else:
        location_filter = "''|''"
    integration_id = location_filter.split('|')[1]
    ### fetch column for account_key
    try:
        account_key_column = SegmentColumnMapping.objects.filter(company_id=company_id, integration_id = integration_id, column_name_inuit='account_key').values('column_name_django').last()['column_name_django']
    except:
        account_key_column = None
    ### fetch column Name for 
    try:
        date_column = SegmentColumnMapping.objects.filter(company_id=company_id, integration_id = integration_id, column_name_inuit='tx_date').values('column_name_django').last()['column_name_django']
    except:
        date_column = None
    ### fetch the amount column 
    try:
        amount_column = SegmentColumnMapping.objects.filter(company_id=company_id, integration_id = integration_id, column_name_inuit='subt_nat_amount').values('column_name_django').last()['column_name_django']
    except:
        amount_column = None 
    convert = True
    print(data)
    try:
        from_date = data['fromDate']
        to_date = data['toDate']
    except:
        from_date = datetime.now() - timedelta(365)
        to_date = datetime.now()
        convert = False
    if convert:
        incoming_date_format = "%m-%d-%Y"
        try:
            from_date = datetime.strptime(from_date, incoming_date_format)
            to_date = datetime.strptime(to_date, incoming_date_format)
        except:
            from_date = datetime.now() - timedelta(365)
            to_date = datetime.now()

    date_format_data = "%Y-%m-%d"

    year_end_date = to_date.year

    start_date = from_date.strftime(date_format_data)
    end_date = to_date.strftime(date_format_data)

    ### creating one year previous
    from_date = from_date - timedelta(365)
    to_date = to_date - timedelta(365)

    start_date_prev = from_date.strftime(date_format_data)
    end_date_prev = to_date.strftime(date_format_data)

    print(from_date)
    print(end_date)

    params = dict(date_column=date_column,
    location_filter= location_filter_query,
    start_date= start_date,
    end_date= end_date,
    amount_column= amount_column,
    account_key_column= account_key_column,
    company_id= company_id,
    integration_id= integration_id,
    start_date_prev= start_date_prev,
    end_date_prev= end_date_prev, 
    year_end_date = year_end_date)


    return params


def fetch_data_from_db(query_name, params):
    
    cursor = connection.cursor()
    query = QueryModel.objects.filter(query_name=query_name).values('query').last()['query']
    if query_name=='fetch_budget_settings_query':
        print(query.format(**params))
        print(params)
    cursor.execute(query.format(**params))
    response = dictfetchall(cursor)
   
    cursor.close()
    connection.close()
    response = pd.DataFrame(response)

    return response


def get_locations(request):
    user_id = request.user.id
    user_data = UserModel.objects.filter(user_id = user_id).values().last()
    company_id = user_data['company_id_id']
    priviledge_id = user_data['priviledge_id_id']
    cursor = connection.cursor()
    query = QueryModel.objects.filter(query_name = 'fetch_locations').values('query').last()['query']
    query_dict = dict(company_id = company_id, priviledge_id = priviledge_id)
    cursor.execute(query.format(**query_dict))
    response = dictfetchall(cursor)
    print(response)
    return response




def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    dict_ = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return dict_



def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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
    else:
        print(response.status_code)
    return response.json()


####### todelete (obsolete and dangerous code) ################3
def create_table(table_type, inuit_company_id, company_id):
    model = IntegrationModel.objects.filter(Q(inuit_company_id = inuit_company_id)).values().last()
    if table_type =='PLParent':

        ### Get API Response
        ### Transform them to a Parent PD DF
        ### create a model with the required fields.
        ### save the same
        _, parent_table, _ = get_pl_detail(inuit_company_id)
    
        fields = {}
        for col in parent_table.columns:
            fields[col.lower()] = models.CharField(max_length=255,  null = True, blank = True)
        
        model = create_model(f'{table_type.lower()}_{company_id}', app_label='api',admin_opts = {}, fields = fields)
        
        try:
            imm = IntegrationMappingModel.objects.filter(company_id_id=company_id, table_type=table_type).values().last()
            imm.columns = list(fields.keys())
            imm.table_id = f'{table_type.lower()}_{company_id}'
            imm.save()
        except Exception as e:
            
            imm = IntegrationMappingModel(company_id_id=company_id, table_type=table_type, columns = list(fields.keys()),
                table_id = f'{table_type.lower()}_{company_id}')
            imm.save()


        pandas_to_model(model, parent_table)


    elif table_type=='PLSegment':
        _, _, segment_table = get_pl_detail(inuit_company_id)
        fields = {}
        for col in segment_table.columns:
            fields[col.lower()] = models.CharField(max_length=255,  null = True, blank = True)
        
        model = create_model(f'{table_type.lower()}_{company_id}', app_label='api', admin_opts = {}, fields = fields)
        try:
            imm = IntegrationMappingModel.objects.filter(company_id_id=company_id, table_type=table_type).values().last()
            imm.columns = list(fields.keys())
            imm.table_id = f'{table_type.lower()}_{company_id}'
            imm.save()
        except:
            
            imm = IntegrationMappingModel(company_id_id=company_id, table_type=table_type, columns = list(fields.keys()),
                table_id = f'{table_type.lower()}_{company_id}')
            imm.save()

        pandas_to_model(model, segment_table)


    elif table_type=='Account':
        res_df = get_account_info(inuit_company_id)
        if res_df is not None:
            fields = {}
            res_df.rename(columns = {'id':'account_key'})
            for col in res_df.columns:
                fields[col.lower()] = models.CharField(max_length=255, blank=True, null=True)
            
            model = create_model(name=f'{table_type.lower()}_{company_id}', app_label='api', admin_opts = {}, fields = fields)
            

            #### Update Mapping Model
            try:
                imm = IntegrationMappingModel.objects.filter(company_id_id=company_id, table_type=table_type).values().last()
                imm.columns = list(fields.keys())
                imm.table_id = f'{table_type.lower()}_{company_id}'
                imm.save()
            except:
                
                imm = IntegrationMappingModel(company_id_id=company_id, table_type=table_type, columns = list(fields.keys()),
                    table_id = f'{table_type.lower()}_{company_id}')
                imm.save()

            pandas_to_model(model, res_df)

######## Code to convert pandas to django model (obsolete)############
def _pandas_to_model(model, df, purge = True):
    ### Delete all the content
    model_obj = model()
    if purge:
        try:
            model_obj.__class__.objects.all().delete()
            
        except:
            call_command('makemigrations')
            call_command('migrate')
            
    else:
        try:
            model_obj.__class__.objects.all()
            
        except:
            call_command('makemigrations')
            call_command('migrate')
            

    ### Create a bulk Creat instance
    column_df = df.columns
    column_mapping = {}
    for col in column_df:
        column_mapping[col.lower()] = col
    
    # Create a list to store model instances
    instances_to_insert = []

    # Iterate through the DataFrame rows and create model instances
    for index, row in df.iterrows():
        instance = model()  # Create an instance of your Django model

        # Populate the instance attributes based on the column_mapping
        for field, column in column_mapping.items():
            setattr(instance, field, row[column])

        # Append the instance to the list
        instances_to_insert.append(instance)
    model_obj.__class__.objects.bulk_create(instances_to_insert)
    call_command('makemigrations')
    call_command('migrate')
    
    
#####Use this code instead ######################
def pandas_to_model(model, df, company_id, integration_id, purge = True):
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
    



######### data retrieval from json ###################

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


############function to fetch PL summary #########################
def get_pl_summary(inuit_company_id):
    
   
    response = _generate_access_token(inuit_company_id)
    access_token = response['access_token']
    
    # authorization 
    auth = "Bearer " + access_token
    base_url = BASE_URL
    
    endpoint = f"/v3/company/{inuit_company_id}/reports/ProfitAndLoss"
    
    query_params = {
    "start_date": "2020-08-01",
    "end_date": "2023-11-11",
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
    account = _get_account_info(inuit_company_id)
    account = account[['Classification', 'AccountType', 'account_key', 'AccountSubType']]
    merged_df = pd.merge(a, account, left_on='account_key', right_on='account_key', how='left')
    merged_df = merged_df.replace(float('NaN'), '')
    merged_df.rename(columns={'Classification':'classification', 'AccountType':'account_type', 'AccountSubType':'account_subtype'}, inplace=True)
    
    return merged_df


########### Json transformer for PL summary ######################3
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
       
    
       
    
    return fulldump



######### main function to fetch PL data from API and store it in tables######################
def get_pl_detail(inuit_company_id, company_id, integration_id,from_db = False, plSummary=False, from_date=None, to_date=None):
    json_response = None
    merge_df = None 
    colDat = None
    if from_db:
        # fetch column mapping
        column_mapping_data = SegmentColumnMapping.objects.all().filter(company_id=company_id).values()
        df = pd.DataFrame(list(column_mapping_data))
        

        #fetch full dump
        segment_data = SegmentData.objects.all().filter(company_id=company_id).values()
        segmentData = pd.DataFrame(list(segment_data))

        segmentData = segmentData[(segmentData['company_id']==str(company_id)) & (segmentData['integration_id']==str(integration_id))]
        
        
        rename_col={}
        for index, row in df.iterrows():
            rename_col[row['column_name_django']] = row['column_name_inuit']

        col_to_drop = []
        for col in segmentData.columns:
            if col not in rename_col.keys():
                col_to_drop.append(col)
        
        segmentData.rename(columns = rename_col, inplace=True)
        segmentData.drop(col_to_drop, axis=1, inplace=True)
        
        segmentData.replace("", float("NaN"), inplace = True)
        segmentData.dropna(how='all', axis = 1, inplace = True)
       
        ### creating colDat
        df.replace('',float('NaN'), inplace=True)
        df.dropna(inplace=True)
        
        colDat = list(df['column_name_inuit'])
        
        
        ### pulling data from parent table
        obj = PLParent.objects.all().filter(company_id= company_id).values()
        parent_df = pd.DataFrame(list(obj))
        
        final_p_df = parent_df[['desc','account_key','index_ui', 'classification']]
        #final_p_df = final_p_df[~(final_p_df['index_ui']=='')].sort_values('index_ui')
        #final_p_df['account_key'] = final_p_df['account_key']
        
        #### create transaction Df
        transaction_df = segmentData[(segmentData['tx_date']!='')]
        transaction_df['subt_nat_amount'] = transaction_df['subt_nat_amount'].astype(float).round(2)

        #### applying date filter
        date_format_data = "%Y-%m-%d"
        transaction_df['tx_date'] = pd.to_datetime(transaction_df['tx_date'], format = date_format_data)

        incoming_date_format = "%m-%d-%Y"

        transaction_df_current = transaction_df[(transaction_df['tx_date'] >= from_date) & (transaction_df['tx_date'] <= to_date)]
        transaction_df_current = transaction_df_current.drop(['tx_date'], axis=1)
        grouped_df_current = transaction_df_current.groupby(['account_key']).sum()
        #### reduce from and to date by a year
        from_date = from_date - timedelta(365)
        to_date = to_date - timedelta(365)


        transaction_df_past = transaction_df[(transaction_df['tx_date'] >= from_date) & (transaction_df['tx_date'] <= to_date)]
        transaction_df_past = transaction_df_past.drop(['tx_date'], axis=1)
        
        grouped_df_past = transaction_df_past.groupby(['account_key']).sum()
        #### merging everthing

        merged_summary_df = pd.merge(final_p_df, grouped_df_current, left_on='account_key', right_on=grouped_df_current.index, how='left')
        merged_summary_df = pd.merge(merged_summary_df, grouped_df_past, left_on='account_key', right_on=grouped_df_past.index, how='left')

        merged_summary_df['subt_nat_amount_x'] = merged_summary_df['subt_nat_amount_x'].astype(float).round(2)
        merged_summary_df['subt_nat_amount_y'] = merged_summary_df['subt_nat_amount_y'].astype(float).round(2)

        
        merged_summary_df['subt_nat_amount_x'] = round(merged_summary_df['subt_nat_amount_x'],2)
        merged_summary_df['subt_nat_amount_y'] = round(merged_summary_df['subt_nat_amount_y'],2)


        
        merged_summary_df = merged_summary_df.replace(float('NaN'), 0)
        merged_summary_df['change'] = (round(merged_summary_df['subt_nat_amount_x'].astype(float) - merged_summary_df['subt_nat_amount_y'].astype(float),2))
        merged_summary_df['per_change'] = round((100*merged_summary_df['change']/merged_summary_df['subt_nat_amount_y'].astype(float)),2)
        merged_summary_df = merged_summary_df.replace(float('inf'), 100)
        merged_summary_df = merged_summary_df.replace(float('-inf'), -100)
        merged_summary_df = merged_summary_df.replace(float('NaN'), 0)
        ### code to populate the subtotals
        ### loop through each row
        #for index, row in merged_summary_df.iterrows():
        #    ## check if the subt_nat_amount_x/y is '-'
        #    if row['subt_nat_amount_x'] == row['subt_nat_amount_y'] and row['subt_nat_amount_x']=='-':
        #        total_subt_x = merged_summary_df[(merged_summary_df['subt_nat_amount_x']!='-') & (merged_summary_df['index_ui_x'].str.startswith(row['selfId_x']))]['subt_nat_amount_x'].sum()
        #        merged_summary_df.at[index, 'subt_nat_amount_x'] = total_subt_x

        #        total_subt_y = merged_summary_df[(merged_summary_df['subt_nat_amount_y']!='-') & (merged_summary_df['index_ui_y'].str.startswith(row['selfId_x']))]['subt_nat_amount_y'].sum()
        #        merged_summary_df.at[index, 'subt_nat_amount_y'] = total_subt_y

        #        classification_temp = merged_summary_df[(merged_summary_df['subt_nat_amount_x']!='-') & (merged_summary_df['index_ui_x'].str.startswith(row['selfId_x']))]['classification']
        #       
        #        classification_temp = classification_temp.drop_duplicates()
        #        merged_summary_df.at[index, 'classification'] = classification_temp.iloc[-1]


        relevant_col = ['desc', 'index_ui', 'change', 'per_change','subt_nat_amount_x','subt_nat_amount_y', 'classification', 'account_key']
        
        merged_summary_df['change'] = (merged_summary_df['subt_nat_amount_x'].astype(float).round(2) - merged_summary_df['subt_nat_amount_y'].astype(float).round(2))
        
        merged_summary_df['per_change'] = (100*merged_summary_df['change']/merged_summary_df['subt_nat_amount_y'])
        merged_summary_df['per_change'] = merged_summary_df['per_change'].astype(float).round(2)
        merged_summary_df['change'] = merged_summary_df['change'].astype(float).round(2)
        
        
        merged_summary_df = merged_summary_df[relevant_col]
        
        #merged_summary_df.rename(columns = {'index_ui_x':'index_ui'}, inplace=True)
        merged_summary_df = merged_summary_df.replace(float('inf'), 100)
        merged_summary_df = merged_summary_df.replace(float('-inf'), -100)
        merged_summary_df = merged_summary_df.replace(float('NaN'), 0)
        merged_summary_df = merged_summary_df.replace(0, '-')
        merged_summary_df = merged_summary_df.replace("", '-')
        merged_summary_df = merged_summary_df[(merged_summary_df['account_key']=='-') | (merged_summary_df['subt_nat_amount_x']!= '-') | (merged_summary_df['subt_nat_amount_y']!='-')]
        col_title = ['Description', 'index_ui', 'Change', 'Percent Change', 'Current', 'Previous year', 'Classification', 'account_key']
       

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
       
        nested_json = create_tree_structure(merged_summary_df, parent_key='')
        columns_response = []
        for val, title in zip(relevant_col, col_title):
            item_col = {}
            item_col['key'] = val
            item_col['value'] = title
            columns_response.append(item_col)
        merged_df = merged_summary_df
        
        

        

    else:
        
        ## check if the data in the parent table exists
        parent_obj = PLParent.objects.all().filter(company_id=company_id).values()
        if parent_obj:
            pl_table = pd.DataFrame(list(parent_obj))
        else:
            pl_table = get_pl_summary(inuit_company_id)
            pandas_to_model(pl_table, "PLParent")


        model = IntegrationModel.objects.filter(Q(inuit_company_id=inuit_company_id)).values().last()

        ### get access token
        
        
        response = generate_access_token(inuit_company_id)
        access_token = response['access_token']

        # authorization 
        auth = "Bearer " + access_token
        base_url = BASE_URL

        endpoint = f"/v3/company/{inuit_company_id}/reports/ProfitAndLossDetail"

        from_date = datetime.now() - timedelta(365)
        to_date = datetime.now()

        inuit_date_format = "%Y-%m-%d"

        query_params = {
        "start_date": from_date.strftime(inuit_date_format),
        "end_date":  to_date.strftime(inuit_date_format),
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
            
            

        nested_json, columns_response, merged_df = _json_transformer(json_response, create_nest = False)

        
        ##### mapping account details to the fulldump ###########

        
        
        list_title = []
        mColumns = merged_df.columns
        
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


        

        pandas_to_model('fulldump', merged_df, company_id, integration_id)


        ### update merged table #######3
        pandas_to_model('column_mapping', column_df, company_id, integration_id)


    return nested_json,columns_response, merged_df


########### query based verion of get_pl
def get_pl_detail_new(request):
    params = generate_params(request)
    relevant_col = ['desc', 'index_ui', 'change', 'per_change','subt_nat_amount_x','subt_nat_amount_y', 'classification', 'account_key']
    col_title = ['Description', 'index_ui', 'Change', 'Percent Change', 'Current', 'Previous year', 'Classification', 'account_key']

    if params['amount_column'] is not None:
        merged_summary_df = fetch_data_from_db('fetch_pl_summary_query', params)
        relevant_col = ['desc', 'index_ui', 'change', 'per_change','subt_nat_amount_x','subt_nat_amount_y', 'classification', 'account_key']
        merged_summary_df = merged_summary_df[relevant_col]
        col_title = ['Description', 'index_ui', 'Change', 'Percent Change', 'Current', 'Previous year', 'Classification', 'account_key']

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
        
        nested_json = create_tree_structure(merged_summary_df, parent_key='')
        merged_df = merged_summary_df

    else:
        nested_json = {}
        merged_df = pd.DataFrame(columns = relevant_col)


    columns_response = []
    for val, title in zip(relevant_col, col_title):
        item_col = {}
        item_col['key'] = val
        item_col['value'] = title
        columns_response.append(item_col)
        
   

    return nested_json,columns_response, merged_df



############ function to generate the PL table (obsolete) #####################

def generate_pl_json(parent_table, segment_table, mini=False):
    try:
        pid = list(segment_table['parentId'].drop_duplicates())
        col = list(segment_table['desc'].drop_duplicates())
    except:
        pid = list(segment_table['parentid'].drop_duplicates())
        col = list(segment_table['desc'].drop_duplicates())
    new_df = {}
    for c in col:
        new_df[c] = np.array(segment_table.groupby('desc').get_group(c)['value'])
    try:
        new_df['parentId'] = np.array(segment_table.groupby('desc').get_group('tx_date')['parentId'])
        new_df['selfId'] = np.array(segment_table.groupby('desc').get_group('tx_date')['selfId'])
        new_df['com_id'] = np.array(segment_table.groupby('desc').get_group('tx_date')['com_id'])
    except:
        new_df['parentid'] = np.array(segment_table.groupby('desc').get_group('tx_date')['parentid'])
        new_df['selfid'] = np.array(segment_table.groupby('desc').get_group('tx_date')['selfid'])
        new_df['com_id'] = np.array(segment_table.groupby('desc').get_group('tx_date')['com_id'])
    child_table = pd.DataFrame.from_dict(new_df)
    
    try:
        merged_df = pd.merge(parent_table, child_table, left_on='selfId', right_on='parentId', how='left', suffixes=('_parent', '_child')).fillna('')
        datUi = []
        for x, y in zip(list(merged_df['selfId_parent']), list(merged_df['selfId_child'])):
            if y != '':
                y = int(y)
                x=x[:-2]
                datUi.append(x+'-'+str(y))
            else:
                datUi.append(x)


    except:
        merged_df = pd.merge(parent_table, child_table, left_on='selfid', right_on='parentid', how='left', suffixes=('_parent', '_child')).fillna('')
        datUi = []
        for x, y in zip(list(merged_df['selfid_parent']), list(merged_df['selfid_child'])):
            if y != '':
                y = int(y)
                x=x[:-2]
                datUi.append(x+'-'+str(y))
            else:
                datUi.append(x)
    
    
    merged_df['index_ui'] = datUi

    
    # Group by selfId_parent to create the nested structure
    if mini:
        nested_json = create_nested_json_pldetail(parent_table, parent_col = 'selfid')
        
    else:
        nested_json = create_nested_json_pldetail(merged_df, parent_col = 'index_ui')

    

    return nested_json, parent_table, segment_table


################ function to create nested json response (obsolete) ######################

def create_nested_json_pldetail(df, parent = None, parent_col = ''):
    res = []

    
    if parent is not None:
        for _, rows in df.iterrows():
            if len(rows[parent_col].split('-')) == len(parent.split('-'))+1 and rows[parent_col].startswith(parent):
                item = {}
                for col in df.columns:
                    item[col] = rows[col]
                if create_nested_json_pldetail(df, parent = rows[parent_col], parent_col = parent_col):
                    item['children'] = create_nested_json_pldetail(df, parent = rows[parent_col], parent_col = parent_col)
                res.append(item)
    else:
        item = {}
        for col in df.columns:
            item[col] = df.iloc[0][col]
        if create_nested_json_pldetail(df, parent = df.iloc[0][parent_col], parent_col = parent_col):
            item['children'] = create_nested_json_pldetail(df, parent = df.iloc[0][parent_col], parent_col = parent_col)
        res.append(item)

    return res


########## to get account info ##############
def get_account_info(inuit_company_id):
    model = IntegrationModel.objects.filter(Q(inuit_company_id=inuit_company_id)).values().last()

    ### get access token
    response = generate_access_token(inuit_company_id)
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


######### function used to create nested json based on json from the api or directly from merged_df ################
def _json_transformer(report =None, merged_df = None, colDat = None, col_df=None, create_nest=True):
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
                try:
                    temp_fd.append(j['id'])
                except:
                    temp_fd.append('')
            fulldump.append(temp_fd)
        colDat.insert(1, 'account_key')
        fulldump = pd.DataFrame(fulldump, columns = colDat)
        
        fulldump[colDat[0]] = [x if is_date(x) else '' for x in fulldump[colDat[0]]]

        merged_df = fulldump


    #### code to convert merges data into nested json starts here ############3
    merged_df.replace(float("NaN"), "", inplace=True)

    
    #### create new index ####
    merged_df['index'] = [x for x in range(len(merged_df))]
    merged_df.set_index('index', inplace = True)
    #### populate the account key at the transaction level ######
    for i in range(len(merged_df)):
        if is_date(merged_df.iloc[i]['tx_date']):
            merged_df.at[i, 'account_key'] = merged_df.at[i-1,'account_key']

    merged_df.dropna(inplace = True)

    merged_df = merged_df[merged_df['tx_date']!='']

    ##### create main tree structure #####
    tree_structure = {}
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

        for val, title in zip(colDat, colTitle):
            item_col = {}
            item_col['key'] = val
            item_col['value'] = title
            columns_response.append(item_col)

    return tree_structure, columns_response, merged_df

########## to check if the value is a date or not ################333
from dateutil.parser import parse
def is_date(string, fuzzy=False):
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