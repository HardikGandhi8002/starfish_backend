# Generated by Django 4.2.5 on 2023-10-25 18:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BenchmarkModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_id', models.CharField(blank=True, max_length=255, null=True)),
                ('integration_id', models.CharField(blank=True, max_length=255, null=True)),
                ('expense_head', models.CharField(blank=True, max_length=255, null=True)),
                ('best_in_class', models.CharField(blank=True, max_length=255, null=True)),
                ('avg_in_class', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BenchmarkModelOverview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_id', models.CharField(blank=True, max_length=255, null=True)),
                ('integration_id', models.CharField(blank=True, max_length=255, null=True)),
                ('avg_cost', models.CharField(blank=True, max_length=255, null=True)),
                ('avg_inc', models.CharField(blank=True, max_length=255, null=True)),
                ('bic_cost', models.CharField(blank=True, max_length=255, null=True)),
                ('bic_inc', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompanyModel',
            fields=[
                ('company_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('email_id', models.CharField(blank=True, null=True, verbose_name='Email ID')),
                ('address_1', models.TextField(max_length=100, verbose_name='Address 1')),
                ('address_2', models.TextField(max_length=100, verbose_name='Address 2')),
                ('country_name', models.CharField(blank=True, max_length=255, null=True)),
                ('state_name', models.TextField(max_length=50, verbose_name='State Name')),
                ('city', models.TextField(max_length=50, verbose_name='City Name')),
                ('zip_code', models.CharField(blank=True, null=True, verbose_name='Zip Code')),
                ('phone_number', models.CharField(blank=True, null=True, verbose_name='Phone number')),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('registration_date', models.DateField(auto_now_add=True, verbose_name='Registration Date')),
                ('activation_date', models.DateField(auto_now_add=True, verbose_name='Activation Date')),
                ('deactivation_date', models.DateField(blank=True, null=True, verbose_name='DeActivation Date')),
                ('registration_ip_address', models.TextField(blank=True, null=True, verbose_name='Registration IP Address')),
                ('activation_ip_address', models.TextField(blank=True, null=True, verbose_name='Activation IP Address')),
                ('deactivate_ip_address', models.TextField(blank=True, null=True, verbose_name='De activate IP Address')),
                ('token', models.TextField(blank=True, null=True, verbose_name='Token name')),
                ('updated_date', models.DateField(auto_now_add=True, verbose_name='Update Date')),
            ],
        ),
        migrations.CreateModel(
            name='CountryModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country_id', models.CharField(blank=True, max_length=5, null=True, verbose_name='Country ID')),
                ('country_label', models.CharField(blank=True, max_length=60, null=True, verbose_name='Country Label')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='latituide')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='latituide')),
            ],
        ),
        migrations.CreateModel(
            name='IntegrationModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('secret_key', models.TextField(blank=True, null=True, verbose_name='Secret key')),
                ('client_id', models.TextField(blank=True, null=True, verbose_name='Client key')),
                ('redirect_uri', models.TextField(blank=True, null=True, verbose_name='Redirect URI')),
                ('integration_type', models.CharField(choices=[('offline', 'Offline'), ('online', 'Online')], max_length=20, verbose_name='Integration Type')),
                ('inuit_company_id', models.CharField(max_length=255, null=True, verbose_name='Inuit Company ID')),
                ('access_token', models.TextField(blank=True, null=True, verbose_name='Access token')),
                ('refresh_token', models.TextField(blank=True, null=True, verbose_name='Refresh token')),
                ('date_updated', models.DateField(auto_now=True, null=True, verbose_name='Date Updated')),
                ('max_update', models.BooleanField(blank=True, default=False, null=True, verbose_name='Max Update')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
            ],
        ),
        migrations.CreateModel(
            name='LocationModel',
            fields=[
                ('location_id', models.BigAutoField(primary_key=True, serialize=False, verbose_name='Location Id')),
                ('description', models.TextField(verbose_name='Description')),
                ('address', models.TextField(verbose_name='Address')),
                ('comments', models.TextField(verbose_name='Comments')),
                ('active', models.BooleanField(verbose_name='Active')),
                ('created_date', models.DateField(verbose_name='Created on')),
                ('updated_date', models.DateField(auto_now_add=True, verbose_name='Created on')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
            ],
        ),
        migrations.CreateModel(
            name='PriviledgeModel',
            fields=[
                ('priviledge_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('description', models.TextField(verbose_name='Description')),
                ('comments', models.TextField(verbose_name='Comments')),
                ('active', models.BooleanField(verbose_name='Active')),
                ('created_date', models.DateField(verbose_name='Created on')),
                ('updated_date', models.DateField(auto_now_add=True, verbose_name='Created on')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationURLModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guid', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('date_generated', models.DateField(auto_now_add=True, null=True)),
                ('used_flag', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='RoleModel',
            fields=[
                ('role_id', models.BigAutoField(primary_key=True, serialize=False, verbose_name='Role ID')),
                ('description', models.TextField(verbose_name='Description')),
                ('active', models.BooleanField(verbose_name='Active')),
                ('created_date', models.DateField(verbose_name='Created Date')),
                ('updated_date', models.DateField(auto_now_add=True, verbose_name='Updated Date')),
            ],
        ),
        migrations.CreateModel(
            name='ScreenModel',
            fields=[
                ('screen_id', models.BigAutoField(primary_key=True, serialize=False, verbose_name='screen_id')),
                ('description', models.TextField(verbose_name='description')),
                ('data_control', models.BooleanField(default=False, verbose_name='data_control')),
                ('active', models.BooleanField(default=False, verbose_name='active')),
            ],
        ),
        migrations.CreateModel(
            name='SegmentColumnMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_id', models.CharField(blank=True, max_length=255, null=True)),
                ('integration_id', models.CharField(blank=True, max_length=255, null=True)),
                ('column_name_django', models.CharField(blank=True, max_length=255, null=True)),
                ('column_name_inuit', models.CharField(blank=True, max_length=255, null=True)),
                ('column_desc_inuit', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SegmentData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_id', models.CharField(blank=True, max_length=255, null=True)),
                ('integration_id', models.CharField(blank=True, max_length=255, null=True)),
                ('col1', models.CharField(blank=True, max_length=255, null=True)),
                ('col2', models.CharField(blank=True, max_length=255, null=True)),
                ('col3', models.CharField(blank=True, max_length=255, null=True)),
                ('col4', models.CharField(blank=True, max_length=255, null=True)),
                ('col5', models.CharField(blank=True, max_length=255, null=True)),
                ('col6', models.CharField(blank=True, max_length=255, null=True)),
                ('col7', models.CharField(blank=True, max_length=255, null=True)),
                ('col8', models.CharField(blank=True, max_length=255, null=True)),
                ('col9', models.CharField(blank=True, max_length=255, null=True)),
                ('col10', models.CharField(blank=True, max_length=255, null=True)),
                ('col11', models.CharField(blank=True, max_length=255, null=True)),
                ('col12', models.CharField(blank=True, max_length=255, null=True)),
                ('col13', models.CharField(blank=True, max_length=255, null=True)),
                ('col14', models.CharField(blank=True, max_length=255, null=True)),
                ('col15', models.CharField(blank=True, max_length=255, null=True)),
                ('col16', models.CharField(blank=True, max_length=255, null=True)),
                ('col17', models.CharField(blank=True, max_length=255, null=True)),
                ('col18', models.CharField(blank=True, max_length=255, null=True)),
                ('col19', models.CharField(blank=True, max_length=255, null=True)),
                ('col20', models.CharField(blank=True, max_length=255, null=True)),
                ('col21', models.CharField(blank=True, max_length=255, null=True)),
                ('col22', models.CharField(blank=True, max_length=255, null=True)),
                ('col23', models.CharField(blank=True, max_length=255, null=True)),
                ('col24', models.CharField(blank=True, max_length=255, null=True)),
                ('col25', models.CharField(blank=True, max_length=255, null=True)),
                ('col26', models.CharField(blank=True, max_length=255, null=True)),
                ('col27', models.CharField(blank=True, max_length=255, null=True)),
                ('col28', models.CharField(blank=True, max_length=255, null=True)),
                ('col29', models.CharField(blank=True, max_length=255, null=True)),
                ('col30', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserModel',
            fields=[
                ('user_id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('first_name', models.CharField(blank=True, max_length=40, null=True, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=40, null=True, verbose_name='Last name')),
                ('email_id', models.EmailField(blank=True, max_length=254, null=True, verbose_name='User Email Id')),
                ('address_1', models.TextField(blank=True, max_length=100, null=True, verbose_name='Address 1')),
                ('address_2', models.TextField(blank=True, max_length=100, null=True, verbose_name='Address 2')),
                ('country_name', models.CharField(blank=True, max_length=255, null=True)),
                ('state_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='State Name')),
                ('city', models.CharField(blank=True, max_length=50, null=True, verbose_name='City Name')),
                ('zip_code', models.IntegerField(blank=True, null=True, verbose_name='Zip Code')),
                ('phone_number', models.IntegerField(blank=True, null=True, verbose_name='Phone Number')),
                ('active', models.BooleanField(blank=True, default=False, null=True, verbose_name='Active')),
                ('registration_date', models.DateField(auto_now_add=True, null=True, verbose_name='Registration Date')),
                ('activation_date', models.DateField(auto_now_add=True, null=True, verbose_name='Activation Date')),
                ('deactivation_date', models.DateField(blank=True, null=True, verbose_name='DeActivation Date')),
                ('registration_ip_address', models.CharField(blank=True, null=True, verbose_name='Registration IP Address')),
                ('activation_ip_address', models.CharField(blank=True, null=True, verbose_name='Activation IP Address')),
                ('deactivate_ip_address', models.CharField(blank=True, null=True, verbose_name='De activate IP Address')),
                ('token', models.CharField(blank=True, null=True, verbose_name='Token name')),
                ('updated_date', models.DateField(auto_now=True, null=True, verbose_name='Update Date')),
                ('comments', models.TextField(blank=True, max_length=255, null=True, verbose_name='Comments')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_id_user', to='api.companymodel')),
                ('created_user_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel')),
                ('priviledge_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.priviledgemodel')),
                ('role_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.rolemodel')),
                ('updated_user_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_update', to='api.usermodel')),
            ],
        ),
        migrations.CreateModel(
            name='TaskManagerModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_title', models.CharField(blank=True, max_length=255, null=True)),
                ('task_desc', models.TextField(blank=True, null=True)),
                ('status', models.CharField(blank=True, max_length=255, null=True)),
                ('due_on', models.CharField(blank=True, max_length=100, null=True)),
                ('date_updated', models.DateField(auto_now=True, null=True, verbose_name='Date Updated')),
                ('created_date', models.DateField(auto_now_add=True, null=True, verbose_name='Created on')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_to_user', to='api.usermodel')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel')),
            ],
        ),
        migrations.CreateModel(
            name='TaskComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, null=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel')),
                ('task_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.taskmanagermodel')),
            ],
        ),
        migrations.CreateModel(
            name='RoleScreenModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.rolemodel')),
                ('screen_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.screenmodel')),
            ],
        ),
        migrations.AddField(
            model_name='rolemodel',
            name='created_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel'),
        ),
        migrations.AddField(
            model_name='rolemodel',
            name='updated_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_user_role', to='api.usermodel'),
        ),
        migrations.CreateModel(
            name='PriviledgeScreenLocModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(verbose_name='Active')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
                ('location_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.locationmodel')),
                ('priviledge_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.priviledgemodel')),
                ('screen_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.screenmodel')),
            ],
        ),
        migrations.AddField(
            model_name='priviledgemodel',
            name='created_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel'),
        ),
        migrations.AddField(
            model_name='priviledgemodel',
            name='updated_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_user_priv', to='api.usermodel'),
        ),
        migrations.CreateModel(
            name='PLParent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selfid', models.CharField(blank=True, max_length=255, null=True)),
                ('desc', models.CharField(blank=True, max_length=255, null=True)),
                ('account_key', models.CharField(blank=True, max_length=255, null=True)),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
                ('integration_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.integrationmodel')),
            ],
        ),
        migrations.CreateModel(
            name='PasswordResetModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_date', models.DateField(verbose_name='Request Date')),
                ('change_date', models.DateField(verbose_name='Request Date')),
                ('request_ip_address', models.TextField(verbose_name='Request IP Address')),
                ('change_ip_address', models.TextField(verbose_name='Change IP Address')),
                ('token', models.TextField(verbose_name='Token')),
                ('link_expiry_date', models.DateField(verbose_name='Link Expiry date')),
                ('user_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel')),
            ],
        ),
        migrations.AddField(
            model_name='locationmodel',
            name='created_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel'),
        ),
        migrations.AddField(
            model_name='locationmodel',
            name='updated_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_user_location', to='api.usermodel'),
        ),
        migrations.AddField(
            model_name='integrationmodel',
            name='user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.usermodel'),
        ),
        migrations.CreateModel(
            name='IntegrationMappingModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('table_id', models.TextField(blank=True, null=True, verbose_name='Table Id')),
                ('columns', models.TextField(blank=True, null=True, verbose_name='Columns')),
                ('table_type', models.CharField(blank=True, null=True, verbose_name='Table Type')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
                ('integration_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.integrationmodel')),
                ('location_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.locationmodel')),
            ],
        ),
        migrations.CreateModel(
            name='IntegrationAPIResponseLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request', models.TextField(blank=True, null=True, verbose_name='Request String')),
                ('response', models.TextField(blank=True, null=True, verbose_name='Response String')),
                ('created_date', models.DateField(verbose_name='Created on')),
                ('company_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.companymodel')),
                ('location_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.locationmodel')),
            ],
        ),
        migrations.AddField(
            model_name='companymodel',
            name='admin_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_user_id', to='api.usermodel'),
        ),
        migrations.AddField(
            model_name='companymodel',
            name='updated_user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_user_id_company', to='api.usermodel'),
        ),
    ]
