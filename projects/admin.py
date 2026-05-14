from django.contrib import admin
from .models import Project, CustomerMaster

@admin.register(CustomerMaster)
class CustomerMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'email', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'mobile_number', 'email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'pid', 'name', 'customer_name', 'project_type', 
        'status', 'date_received', 'target_completion_date'
    )
    list_filter = ('status', 'project_type', 'date_received')
    search_fields = ('pid', 'name', 'customer_name', 'customer_part_no', 'pcepl_part_no')
    readonly_fields = ('pid', 'month_received', 'created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pid', 'name', 'customer_name', 'project_type', 'status', 'created_by')
        }),
        ('Part Details', {
            'fields': ('customer_part_no', 'pcepl_part_no')
        }),
        ('Technical Details', {
            'fields': ('inspection_authority', 'applicable_standard')
        }),
        ('Timeline', {
            'fields': ('date_received', 'month_received', 'target_completion_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
