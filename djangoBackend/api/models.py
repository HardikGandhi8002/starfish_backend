from django.db import models
from django.contrib.auth.models import PermissionsMixin, User, AbstractUser
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.utils import timezone
from django.conf import settings
from django.contrib import admin
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core.management import sql, color
from django.db import connection, migrations



class QueryModel(models.Model):
    query_name = models.CharField(max_length = 255)
    query = models.TextField(verbose_name = "Query")
    


# Create your models here.
class UserManager(BaseUserManager):

    use_in_migration = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is Required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff = True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser = True')

        return self.create_user(email, password, **extra_fields)

class CountryModel(models.Model):
    country_id = models.CharField(
        verbose_name="Country ID", max_length=5, null=True, blank=True
    )
    country_label = models.CharField(verbose_name="Country Label", max_length=60, null=True, blank=True)
    latitude = models.FloatField(verbose_name='latituide', null=True, blank=True)
    longitude = models.FloatField(verbose_name='latituide', null=True, blank=True)



class UserModel(models.Model):
    user_id = models.OneToOneField(User,on_delete=models.CASCADE, primary_key=True)
    company_id = models.ForeignKey(
        "CompanyModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_id_user",
    )
    role_id = models.ForeignKey("RoleModel", on_delete=models.SET_NULL, null = True, blank = True)
    priviledge_id = models.ForeignKey("PriviledgeModel", on_delete=models.SET_NULL, null = True, blank = True)
    first_name = models.TextField(verbose_name="First name", null=True, blank=True)
    last_name = models.TextField(verbose_name="Last name", null=True, blank=True)
    email_id = models.EmailField(verbose_name="User Email Id", null=True, blank=True)
    address_1 = models.TextField(verbose_name="Address 1", max_length=100, null=True, blank=True)
    address_2 = models.TextField(verbose_name="Address 2", max_length=100, null=True, blank=True)
    #country_id = models.ForeignKey(
    #    CountryModel,
    #    on_delete=models.SET_NULL,
    #    null=True,
    #    blank=True,
    #    verbose_name="Country ID",
    #    related_name="country_id_user",
    #)
    country_name = models.CharField(max_length=255, null=True, blank=True)
    state_name = models.CharField(verbose_name="State Name", max_length=50, null=True, blank=True)
    city = models.CharField(verbose_name="City Name", max_length=50, null=True, blank=True)
    zip_code = models.IntegerField(verbose_name="Zip Code", null=True, blank=True)
    phone_number = models.CharField(verbose_name="Phone Number", null=True, blank=True, max_length=20)
    active = models.BooleanField(verbose_name="Active", default=False, null=True, blank=True)
    registration_date = models.DateField(verbose_name="Registration Date", null=True, blank=True, auto_now_add=True)
    activation_date = models.DateField(verbose_name="Activation Date", null=True, blank=True, auto_now_add=True)
    deactivation_date = models.DateField(verbose_name="DeActivation Date", null=True, blank=True)
    registration_ip_address = models.CharField(verbose_name="Registration IP Address", null=True, blank=True)
    activation_ip_address = models.CharField(verbose_name="Activation IP Address", null=True, blank=True)
    deactivate_ip_address = models.CharField(verbose_name="De activate IP Address", null=True, blank=True)
    token = models.CharField(verbose_name="Token name", null=True, blank=True)
    updated_date = models.DateField(verbose_name="Update Date", null=True, blank=True, auto_now=True)
    updated_user_id = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_update"
    )
    comments = models.TextField(verbose_name="Comments", max_length=255, null=True, blank=True)
    created_user_id = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
   )
    def __str__(self):
        return self.first_name

class CompanyModel(models.Model):
    company_id = models.BigAutoField(primary_key=True)
    name=models.TextField(null=True, blank=True)
    admin_user_id = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        related_name="admin_user_id",
        null=True,
        blank=True,
    )
    email_id = models.TextField(verbose_name="Email ID", null=True, blank=True)
    address_1 = models.TextField(verbose_name="Address 1", max_length=100)
    address_2 = models.TextField(verbose_name="Address 2", max_length=100)
    #country_id = models.ForeignKey(
    #    CountryModel,
    #    on_delete=models.SET_NULL,
    #    null=True,
    #    blank=True,
    #    verbose_name="Country ID",
    #    related_name="country_id_company",
    #)
    country_name=models.CharField(max_length=255, null=True, blank=True)
    state_name = models.TextField(verbose_name="State Name", max_length=50)
    city = models.TextField(verbose_name="City Name", max_length=50)
    zip_code = models.CharField(verbose_name="Zip Code", null=True, blank=True, max_length=50)
    phone_number = models.CharField(verbose_name="Phone number", null=True, blank=True, max_length=50)
    active = models.BooleanField(verbose_name="Active", default=False)
    registration_date = models.DateField(verbose_name="Registration Date", auto_now_add=True)
    activation_date = models.DateField(verbose_name="Activation Date", auto_now_add=True)
    deactivation_date = models.DateField(verbose_name="DeActivation Date", null = True, blank=True)
    registration_ip_address = models.TextField(verbose_name="Registration IP Address", null=True, blank=True)
    activation_ip_address = models.TextField(verbose_name="Activation IP Address", null=True, blank=True)
    deactivate_ip_address = models.TextField(verbose_name="De activate IP Address", null=True, blank=True)
    token = models.TextField(verbose_name="Token name", null=True, blank=True)
    updated_date = models.DateField(verbose_name="Update Date",auto_now_add=True)
    updated_user_id = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        related_name="updated_user_id_company",
        null=True,
        blank=True,
    )

    ### Test




class ScreenModel(models.Model):
    screen_id = models.BigAutoField(verbose_name="screen_id", primary_key = True)
    description = models.TextField(verbose_name="description")
    data_control = models.BooleanField(verbose_name="data_control", default=False)
    active = models.BooleanField(verbose_name="active", default=False)

class PasswordResetModel(models.Model):
    user_id = models.ForeignKey("UserModel", on_delete=models.SET_NULL, null = True, blank = True)
    request_date = models.DateField(verbose_name="Request Date")
    change_date = models.DateField(verbose_name="Request Date")
    request_ip_address = models.TextField(verbose_name="Request IP Address")
    change_ip_address = models.TextField(verbose_name="Change IP Address")
    token = models.TextField(verbose_name="Token")
    link_expiry_date = models.DateField(verbose_name="Link Expiry date")

class RoleModel(models.Model):
    role_id = models.BigAutoField(verbose_name="Role ID", primary_key=True)
    description = models.TextField(verbose_name="Description")
    active = models.BooleanField(verbose_name="Active")
    created_date = models.DateField(verbose_name="Created Date")
    created_user_id = models.ForeignKey("UserModel", on_delete=models.SET_NULL, null=True, blank=True)
    updated_date = models.DateField(verbose_name="Updated Date",auto_now_add=True)
    updated_user_id = models.ForeignKey("UserModel", on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_user_role")

class RoleScreenModel(models.Model):
    role_id = models.ForeignKey('RoleModel', on_delete=models.SET_NULL, null=True, blank=True)
    screen_id = models.ForeignKey('ScreenModel', on_delete=models.SET_NULL, null=True, blank=True)


class LocationModel(models.Model):
    location_id = models.BigAutoField(verbose_name='Location Id', primary_key = True)
    company_id = models.CharField(null = True, blank = True, max_length = 20)
    integration_id = models.CharField(null = True, blank = True, max_length = 20)
    #internal_id = models.
    description = models.TextField(verbose_name='Description') ## app_name
    col_placement = models.TextField(verbose_name = "Location Placement", null=True, blank=True) # ''
    filter_query = models.TextField(verbose_name = "Filter Query", null=True, blank=True) # ''
    ui_display = models.TextField(verbose_name = "ui Query", null=True, blank=True) # app_name
    created_date = models.DateField(verbose_name='Created on', auto_now_add = True)
    created_user_id = models.CharField(null = True, blank = True, max_length = 20)
    
class PriviledgeModel(models.Model):
    priviledge_id = models.BigAutoField(primary_key=True)
    company_id = models.ForeignKey('CompanyModel', on_delete=models.SET_NULL, null = True, blank = True)
    description = models.TextField(verbose_name="Description")
    active = models.BooleanField(verbose_name="Active", default = False)
    created_date = models.DateField(verbose_name='Created on')
    created_user_id = models.ForeignKey('UserModel', on_delete=models.SET_NULL, null=True, blank=True)
    updated_date = models.DateField(verbose_name='Created on',auto_now_add=True)
    updated_user_id = models.ForeignKey('UserModel', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_user_priv')

class PriviledgeIntegrationMappingModel(models.Model):
    priviledge_id = models.ForeignKey("PriviledgeModel", on_delete=models.SET_NULL, null=True, blank=True)
    integration_id = models.ForeignKey("IntegrationModel",  on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(verbose_name="Active", default = False)

class PriviledgeLocationMappingModel(models.Model):
    priviledge_id = models.ForeignKey("PriviledgeModel", on_delete=models.SET_NULL, null=True, blank=True)
    integration_id = models.ForeignKey("IntegrationModel",  on_delete=models.SET_NULL, null=True, blank=True)
    location_id = models.ForeignKey("LocationModel",  on_delete=models.SET_NULL, null=True, blank=True)


class BudgetModel(models.Model):
    plparent_id = models.ForeignKey("PLParent", on_delete=models.SET_NULL, null=True, blank=True)
    location_id = models.ForeignKey("LocationModel",  on_delete=models.SET_NULL, null=True, blank=True)
    integration_id = models.ForeignKey("IntegrationModel",  on_delete=models.SET_NULL, null=True, blank=True)
    company_id = models.ForeignKey('CompanyModel', on_delete=models.SET_NULL, null = True, blank = True)
    
class BudgetByYearModel(models.Model):
    buget_id = models.ForeignKey("BudgetModel", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.IntegerField(verbose_name = "Year")
    amount = models.FloatField(verbose_name = "Amount")

class RevenueModel(models.Model):
    plparent_id = models.ForeignKey("PLParent", on_delete=models.SET_NULL, null=True, blank=True)
    location_id = models.ForeignKey("LocationModel",  on_delete=models.SET_NULL, null=True, blank=True)
    integration_id = models.ForeignKey("IntegrationModel",  on_delete=models.SET_NULL, null=True, blank=True)
    company_id = models.ForeignKey('CompanyModel', on_delete=models.SET_NULL, null = True, blank = True)
    
class RevenueByYearModel(models.Model):
    buget_id = models.ForeignKey("RevenueModel", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.IntegerField(verbose_name = "Year")
    amount = models.FloatField(verbose_name = "Amount")




class PriviledgeScreenLocModel(models.Model):
    priviledge_id = models.ForeignKey('PriviledgeModel', on_delete=models.SET_NULL, null=True, blank=True)
    company_id = models.ForeignKey('CompanyModel', on_delete=models.SET_NULL, null=True, blank=True)
    integration_id = models.ForeignKey('IntegrationModel', on_delete=models.SET_NULL, null=True, blank=True)
    screen_id = models.ForeignKey('ScreenModel', on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(verbose_name="Active")
 


class IntegrationAPIResponseLog(models.Model):
    company_id = models.ForeignKey('CompanyModel', on_delete=models.SET_NULL, null=True, blank=True)
    location_id = models.ForeignKey('LocationModel', on_delete=models.SET_NULL, null=True, blank=True)
    request = models.TextField(verbose_name='Request String', null=True, blank=True)
    response = models.TextField(verbose_name='Response String', null=True, blank=True)
    created_date = models.DateField(verbose_name='Created on', auto_now_add=True, null = True)

class IntegrationModel(models.Model):
    app_name = models.TextField(blank = True, null= True)
    user_id = models.ForeignKey("UserModel", on_delete=models.SET_NULL, null = True, blank = True)
    secret_key = models.TextField(verbose_name='Secret key', null=True, blank=True)
    client_id = models.TextField(verbose_name='Client key', null=True, blank=True)
    redirect_uri = models.TextField(verbose_name='Redirect URI', null=True, blank=True)
    integration_choices = (('offline', 'Offline'), ('online', 'Online'))
    integration_type = models.CharField(verbose_name='Integration Type', max_length=20, choices = integration_choices)
    inuit_company_id = models.CharField(verbose_name='Inuit Company ID', max_length=255, null = True)
    access_token = models.TextField(verbose_name='Access token', null=True, blank=True)
    refresh_token = models.TextField(verbose_name='Refresh token', null=True, blank=True)
    company_id = models.ForeignKey("CompanyModel", on_delete=models.SET_NULL, null = True, blank = True)
    max_update = models.BooleanField(verbose_name="Max Update", null=True, blank=True, default=False)
    capture_location = models.BooleanField(verbose_name="Capture Location", null=True, blank=True, default=False)
    location_attr = models.BooleanField(verbose_name="Location Attribute", null=True, blank=True, default=False)
    date_updated = models.DateField(verbose_name='Date Updated', auto_now = True, null=True, blank=True)


class IntegrationExcelUploadModel(models.Model):
    company_id = models.ForeignKey("CompanyModel", on_delete=models.SET_NULL, null = True, blank = True)
    integration_id = models.ForeignKey("IntegrationModel", on_delete=models.SET_NULL, null = True, blank = True)
    from_date = models.CharField(verbose_name = "From Date", max_length=100, blank = True, null = True)
    to_date = models.CharField(verbose_name = "To Date", max_length=100, blank = True, null = True)
    upload_status = models.BooleanField(default=False)
    user_file = models.FileField(verbose_name="User Uploaded File", blank = True, null = True, upload_to='user_uploads')
    date_updated = models.DateField(verbose_name='Date Updated', auto_now = True, null=True, blank=True)
    date_added = models.DateField(verbose_name='Date added', auto_now_add = True, null=True, blank=True)
    transformed_file = models.FileField(verbose_name="Transformed Excel File", blank = True, null = True, upload_to='transformed_uploads')
    db_sync = models.BooleanField(default=False)
    remarks = models.TextField()

class FileModel(models.Model):
    company_id = models.ForeignKey("CompanyModel", on_delete=models.SET_NULL, null = True, blank = True)
    integration_id = models.ForeignKey("IntegrationModel", on_delete=models.SET_NULL, null = True, blank = True)
    user_file = models.FileField(verbose_name = "User Field", upload_to='user_uploads')

########obsolete##########
class IntegrationMappingModel(models.Model):
    integration_id = models.ForeignKey('IntegrationModel', on_delete=models.SET_NULL, null = True, blank = True)
    company_id = models.ForeignKey('CompanyModel', on_delete=models.SET_NULL, null=True, blank=True)
    location_id = models.ForeignKey('LocationModel', on_delete=models.SET_NULL, null=True, blank=True)
    table_id = models.TextField(verbose_name="Table Id", null=True, blank=True)
    columns = models.TextField(verbose_name='Columns', null=True, blank=True)
    table_type = models.CharField(verbose_name='Table Type',null=True, blank=True)


class SegmentData(models.Model):
    company_id = models.CharField(max_length=255, null=True, blank=True)
    integration_id = models.CharField(max_length=255, null=True, blank=True)
    col1 = models.TextField( null=True, blank=True)
    col2 = models.TextField( null=True, blank=True)
    col3 = models.TextField( null=True, blank=True)
    col4 = models.TextField( null=True, blank=True)
    col5 = models.TextField( null=True, blank=True)
    col6 = models.TextField( null=True, blank=True)
    col7 = models.TextField( null=True, blank=True)
    col8 = models.TextField( null=True, blank=True)
    col9 = models.TextField( null=True, blank=True)
    col10 = models.TextField( null=True, blank=True)
    col11 = models.TextField( null=True, blank=True)
    col12 = models.TextField( null=True, blank=True)
    col13 = models.TextField( null=True, blank=True)
    col14 = models.TextField( null=True, blank=True)
    col15 = models.TextField( null=True, blank=True)
    col16 = models.TextField( null=True, blank=True)
    col17 = models.TextField( null=True, blank=True)
    col18 = models.TextField( null=True, blank=True)
    col19 = models.TextField( null=True, blank=True)
    col20 = models.TextField( null=True, blank=True)
    col21 = models.TextField( null=True, blank=True)
    col22 = models.TextField( null=True, blank=True)
    col23 = models.TextField( null=True, blank=True)
    col24 = models.TextField( null=True, blank=True)
    col25 = models.TextField( null=True, blank=True)
    col26 = models.TextField( null=True, blank=True)
    col27 = models.TextField( null=True, blank=True)
    col28 = models.TextField( null=True, blank=True)
    col29 = models.TextField( null=True, blank=True)
    col30 = models.TextField( null=True, blank=True)
    
##########obsolete##########
class PLParent(models.Model):
    company_id = models.CharField(max_length=1024, null=True, blank=True)
    integration_id = models.CharField(max_length=1024, null=True, blank=True)
    index_ui = models.CharField(max_length=1024, null=True, blank=True)
    desc = models.CharField(max_length=1024, null=True, blank=True)
    account_key = models.CharField(max_length=1024, null=True, blank=True)
    classification = models.CharField(max_length=1024, null=True, blank=True)	
    account_type = models.CharField(max_length=1024, null=True, blank=True)	
    account_subtype = models.CharField(max_length=1024, null=True, blank=True)
    #total = models.CharField(max_length=255, null=True, blank=True) -- Removed 
    
class SegmentColumnMapping(models.Model):
    company_id = models.CharField(max_length=255, null=True, blank=True)
    integration_id = models.CharField(max_length=255, null=True, blank=True)
    column_name_django = models.CharField(max_length=1024, null=True, blank=True)
    column_name_inuit = models.CharField(max_length=1024, null=True, blank=True)
    column_desc_inuit = models.CharField(max_length=1024, null=True, blank=True)


class BenchmarkModel(models.Model):
    company_id = models.CharField(max_length=255, null=True, blank=True)
    integration_id = models.CharField(max_length=255, null=True, blank=True)
    expense_head = models.CharField(max_length=255, null=True, blank=True)
    best_in_class = models.CharField(max_length=255, null=True, blank=True)
    avg_in_class = models.CharField(max_length=255, null=True, blank=True)

class BenchmarkModelOverview(models.Model):
    company_id = models.CharField(max_length=255, null=True, blank=True)
    integration_id = models.CharField(max_length=255, null=True, blank=True)
    avg_cost = models.CharField(max_length=255, null=True, blank=True)
    avg_inc = models.CharField(max_length=255, null=True, blank=True)
    bic_cost = models.CharField(max_length=255, null=True, blank=True)
    bic_inc = models.CharField(max_length=255, null=True, blank=True)




class RegistrationURLMainModel(models.Model):
    guid = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    date_generated = models.DateField(auto_now_add=True, null=True, blank=True)
    token_used_flag = models.BooleanField(default=False)
    flag = models.BooleanField(default=False)

def create_model(name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (models.Model,), attrs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass
        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model

#class UserData(AbstractUser):
#
#    username = None
#    #user_id = models.BigAutoField(primary_key = True)
#    email = models.EmailField(max_length=100, unique=True)
#    date_joined = models.DateTimeField(auto_now_add=True)
#    is_admin = models.BooleanField(default=False)
#    is_active = models.BooleanField(default=True)
#    is_staff = models.BooleanField(default=False)
#    is_superuser = models.BooleanField(default=False)
#    
#    objects = UserManager()
#    
#    USERNAME_FIELD = 'email'
#    REQUIRED_FIELDS = []
#
#    def __str__(self):
#        return self.email
#
def install(model, table_name = ''):
    from django.core.management import sql, color
    from django.db import connection, migrations

    # Standard syncdb expects models to be in reliable locations,
    # so dynamic models need to bypass django.core.management.syncdb.
    # On the plus side, this allows individual models to be installed
    # without installing the entire project structure.
    # On the other hand, this means that things like relationships and
    # indexes will have to be handled manually.
    # This installs only the basic table definition.

    # disable terminal colors in the sql statements

    operations = [
            migrations.CreateModel(
                name=table_name,
                fields=[
                    (field_name, field)
                    for field_name, field in model.__dict__.items()
                    if isinstance(field, models.Field)
                ],
                options={'db_table': table_name},
            ),
        ]



    with connection.schema_editor() as editor:
        editor.create_model(model, operations[0])


def create_dynamic_model(table_name, fields):
    # Define the meta options for the model.
    class Meta:
        db_table = table_name

    # Create a dictionary to store the fields for the model.
    model_fields = {'__module__': __name__, 'Meta': Meta}

    # Add the fields to the model dictionary.
    for field_name, field_type in fields.items():
        model_fields[field_name] = field_type

    # Create the dynamic model class.
    dynamic_model = type(table_name, (models.Model,), model_fields)

    return dynamic_model

class Command(BaseCommand):
    help = 'Create a migration and apply for dynamic model'

    def handle(self, *args, **kwargs):
        table_name = "book"
        app_label = "api"  # Replace with the actual app label

        # Define the dynamic model fields
        fields = {
            "title": models.CharField(max_length=255),
            "author": models.CharField(max_length=255),
            "published_year": models.IntegerField(),
        }

        class Meta:
            db_table = table_name

        dynamic_model = type(table_name, (models.Model,), {
            **fields,
            '__module__': apps.get_app_config(app_label).name,
            'Meta': Meta,
        })

        # Create the migration operations
        operations = [
            migrations.CreateModel(
                name=table_name,
                fields=[
                    (field_name, field)
                    for field_name, field in fields.items()
                ],
                options={'db_table': table_name},
            ),
        ]

        # Apply the migration operations
        from_state = migrations.state.ProjectState()
        to_state = migrations.state.ProjectState()
        for operation in operations:
            operation.state_forwards(app_label, from_state)
            operation.database_forwards(app_label, schema_editor=None, from_state=from_state, to_state=to_state)

        self.stdout.write(self.style.SUCCESS('Migration created and applied for dynamic model.'))


class TaskManagerModel(models.Model):
    task_title = models.CharField(max_length=255, null = True, blank=True)
    task_desc = models.TextField(null = True, blank=True)
    created_by = models.ForeignKey('UserModel', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey('UserModel', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_to_user')
    status = models.CharField(max_length=255, null = True, blank=True)
    company_id = models.ForeignKey('CompanyModel', on_delete=models.SET_NULL, null = True, blank=True)
    due_on = models.CharField(max_length=100, null=True, blank=True)
    date_updated = models.DateField(verbose_name='Date Updated', auto_now = True, null=True, blank=True)
    created_date = models.DateField(verbose_name='Created on', auto_now_add=True, null=True, blank=True)

class TaskComment(models.Model):
    task_id = models.ForeignKey('TaskManagerModel', on_delete=models.SET_NULL, null = True, blank=True)
    author = models.ForeignKey('UserModel',on_delete=models.SET_NULL, null = True, blank=True)
    comment = models.TextField(null = True, blank=True)
    
