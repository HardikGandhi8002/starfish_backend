"""
URL configuration for djangoBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    . Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    . Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    . Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import *
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("test/", test, name="tester"),
    path("screens/", get_screens, name='user_screen'),
    path("pltable/", fetch_plDetail, name='plTable'),
    path("budget_data/", fetch_budget, name='budget'),
    #re_path(r"callback/$", auth, name='authHandler'),
    path("inuit_auth/", generate_url, name = 'inuit_auth'),
    path('fetch_tokens/', fetch_integration_keys, name='fetch_tokens'),
    path('overview_data/', fetch_overview_new, name='overview'),
    path('benchmark_data/', fetch_benchmark_new, name='benchmark'),
    path('auth/', auth, name='callback_handler'),
    path('get_users/', get_users, name='get_users'),
    path('get_tasks/', get_tasks, name='get_tasks'),
    path('modify_task/', save_task, name='modify_task'),
    path('get_transactions/', fetch_transactions, name='get_transactions'),
    path('miniReg/', trigger_mail, name='trigger_mail'),
    path('verifyCode/', check_guid, name='check_guid'),
    path('regData/', reg_data, name='reg_data'),
    path('country/', get_country, name='get_country'),
    path('auth_update/', roles_auth_handler_edit, name='role_auth_handler'),
    path('add_integration/', save_integration, name='save_integration'),
    path('fetch_excel_data/', fetch_excel_data, name='excel_upload_dump'),
    path('fetch_excel_data/', fetch_excel_data, name='excel_upload_dump'),
    path('xls_fileupload_user/', file_upload_user, name='excel_upload_dump'),
    path('xls_filedownload/<str:id>/', file_download, name='excel_download_dump'),
    path('fetch_auth_data/', fetch_auth_data, name='auth_data'),
    path('add_user/', add_user, name='add_user'),
    path('fetch_locations/', fetch_locations, name='fetch_locations'),
    path('fetch_budget_settings/', fetch_budget_settings, name='fetch_budget_settings'),
    path('set_budget_settings/', set_budget_settings, name='set_budget_settings')
] 