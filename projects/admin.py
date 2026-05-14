from django.contrib import admin
from .models import Project, WorkflowStage, ActivityLog

class WorkflowStageInline(admin.TabularInline):
    model = WorkflowStage
    extra = 0
    fields = ('name', 'order', 'status', 'unlocked_at', 'completed_at')
    readonly_fields = ('unlocked_at', 'completed_at')

class ActivityLogInline(admin.TabularInline):
    model = ActivityLog
    extra = 0
    readonly_fields = ('user', 'action', 'details', 'timestamp')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'pid', 'name', 'customer_name', 'project_type', 
        'status', 'date_received', 'target_completion_date'
    )
    list_filter = ('status', 'project_type', 'date_received')
    search_fields = ('pid', 'name', 'customer_name', 'customer_part_no', 'pcepl_part_no')
    readonly_fields = ('pid', 'month_received', 'created_at', 'updated_at', 'created_by')
    
    inlines = [WorkflowStageInline, ActivityLogInline]
    
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

@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'order', 'status')
    list_filter = ('status', 'name')
    search_fields = ('project__pid', 'name')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('project__pid', 'user__email', 'action')
    readonly_fields = ('project', 'user', 'action', 'details', 'timestamp')
