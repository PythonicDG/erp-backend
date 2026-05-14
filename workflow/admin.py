from django.contrib import admin
from .models import StageTemplate, FormField, StageInstance, StageSubmission, StageActivity

class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 1

@admin.register(StageTemplate)
class StageTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'order', 'assigned_role', 'is_active')
    inlines = [FormFieldInline]

@admin.register(StageInstance)
class StageInstanceAdmin(admin.ModelAdmin):
    list_display = ('project', 'template', 'status', 'order')
    list_filter = ('status', 'template')

@admin.register(StageSubmission)
class StageSubmissionAdmin(admin.ModelAdmin):
    list_display = ('stage_instance', 'submitted_by', 'status', 'submitted_at')
    readonly_fields = ('submitted_at', 'updated_at')

@admin.register(StageActivity)
class StageActivityAdmin(admin.ModelAdmin):
    list_display = ('stage_instance', 'performed_by', 'action', 'timestamp')
