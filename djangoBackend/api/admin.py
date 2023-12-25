from django.contrib import admin

from .models import * 
from import_export.admin import ImportExportModelAdmin
# Register your models here.

class ListAdminMixin(ImportExportModelAdmin):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields]
        super(ListAdminMixin, self).__init__(model, admin_site)


models = (RoleModel, ScreenModel, PasswordResetModel, CompanyModel, 
        UserModel, CountryModel, LocationModel, PriviledgeModel, PriviledgeScreenLocModel, RoleScreenModel, IntegrationModel, 
        IntegrationAPIResponseLog, IntegrationMappingModel, SegmentColumnMapping, SegmentData, BenchmarkModel,
        BenchmarkModelOverview, TaskManagerModel, RegistrationURLMainModel, PLParent, IntegrationExcelUploadModel, FileModel, LocationModel,
        BudgetModel, BudgetByYearModel, PriviledgeIntegrationMappingModel, PriviledgeLocationMappingModel, QueryModel, RevenueByYearModel, RevenueModel)
for model in models:
    admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
    try:
        admin.site.register(model, admin_class)
    except:
        pass

class QueryAdmin(admin.ModelAdmin):
    list_editable = ('query')