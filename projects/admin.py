from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    CustomerMaster,
    Project,
    StandardMaster,
    InspectionAuthorityMaster,
    ECN
)


class ECNInline(admin.TabularInline):
    """Allows viewing and editing ECNs directly within the Project detail page."""
    model = ECN
    extra = 0
    fields = ('ecn_number', 'raised_department', 'change_initiated_by', 'ecn_date', 'status')
    readonly_fields = ('ecn_number', 'raised_department', 'change_initiated_by', 'ecn_date', 'status')
    show_change_link = True
    can_delete = False
    verbose_name = _("Associated Engineering Change Request")
    verbose_name_plural = _("Associated Engineering Change Requests")


@admin.register(CustomerMaster)
class CustomerMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'mobile_number', 'email', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'mobile_number', 'email', 'remarks')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)


@admin.register(StandardMaster)
class StandardMasterAdmin(admin.ModelAdmin):
    list_display = ('standard_number', 'standard_name', 'revision', 'release_year', 'category', 'status')
    list_filter = ('category', 'status', 'release_year')
    search_fields = ('standard_number', 'standard_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('standard_number',)


@admin.register(InspectionAuthorityMaster)
class InspectionAuthorityMasterAdmin(admin.ModelAdmin):
    list_display = ('authority_id', 'name', 'category', 'contact_person', 'applicable_standard', 'status')
    list_filter = ('category', 'status')
    search_fields = ('authority_id', 'name', 'contact_person', 'remarks')
    autocomplete_fields = ('applicable_standard',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('authority_id',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'pid', 'name', 'customer', 'project_type', 
        'status', 'priority', 'date_received', 'target_completion_date'
    )
    list_filter = ('status', 'project_type', 'priority', 'date_received')
    search_fields = ('pid', 'name', 'customer__name', 'customer_name', 'customer_part_no', 'pcepl_part_no')
    readonly_fields = ('pid', 'month_received', 'created_at', 'updated_at')
    autocomplete_fields = ('customer', 'standard', 'inspection_authority_fk', 'created_by', 'supervisor', 'assigned_employee')
    
    inlines = [ECNInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pid', 'name', 'project_type', 'status', 'priority', 'description')
        }),
        ('Customer Details', {
            'fields': ('customer', 'customer_name', 'customer_part_no', 'pcepl_part_no')
        }),
        ('Technical & Compliance', {
            'fields': ('standard', 'applicable_standard', 'inspection_authority_fk', 'inspection_authority')
        }),
        ('Team Assignment', {
            'fields': ('created_by', 'supervisor', 'assigned_employee')
        }),
        ('Timeline', {
            'fields': ('date_received', 'month_received', 'target_completion_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ECN)
class ECNAdmin(admin.ModelAdmin):
    list_display = (
        'ecn_number', 'project', 'raised_department', 
        'change_initiated_by', 'ecn_date', 'status_badge', 'created_at'
    )
    list_filter = ('status', 'raised_department', 'ecn_date', 'created_at')
    search_fields = (
        'ecn_number', 'project__name', 'project__pid', 
        'change_initiated_by', 'raised_department', 
        'old_revision_no', 'new_revision'
    )
    readonly_fields = (
        'ecn_number', 'created_at', 'updated_at', 
        'formatted_details_of_change', 'formatted_impact_analysis', 'formatted_action_plan'
    )
    autocomplete_fields = ('project', 'initiator', 'reviewed_by', 'approved_by')
    
    actions = ['make_submitted', 'make_reviewed', 'make_approved', 'make_rejected']

    @admin.action(description="Mark selected ECNs as Submitted")
    def make_submitted(self, request, queryset):
        updated = queryset.update(status='Submitted')
        self.message_user(request, f"{updated} ECNs successfully marked as Submitted.")

    @admin.action(description="Mark selected ECNs as Reviewed")
    def make_reviewed(self, request, queryset):
        updated = queryset.update(status='Reviewed', reviewed_by=request.user)
        self.message_user(request, f"{updated} ECNs successfully marked as Reviewed.")

    @admin.action(description="Mark selected ECNs as Approved")
    def make_approved(self, request, queryset):
        updated = queryset.update(status='Approved', approved_by=request.user)
        self.message_user(request, f"{updated} ECNs successfully marked as Approved.")

    @admin.action(description="Mark selected ECNs as Rejected")
    def make_rejected(self, request, queryset):
        updated = queryset.update(status='Rejected')
        self.message_user(request, f"{updated} ECNs successfully marked as Rejected.")

    def status_badge(self, obj):
        colors = {
            'Draft': '#6b7280',      # gray
            'Submitted': '#f59e0b',  # amber/yellow
            'Reviewed': '#3b82f6',   # blue
            'Approved': '#10b981',   # emerald/green
            'Rejected': '#ef4444',   # red
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px; display: inline-block; text-align: center; min-width: 80px;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    fieldsets = (
        ('ECN Info & Project Link', {
            'fields': ('ecn_number', 'status', 'project')
        }),
        ('Request Details', {
            'fields': ('raised_department', 'change_initiated_by', 'ecn_date')
        }),
        ('Revision Tracking', {
            'fields': ('old_revision_no', 'old_revision_date', 'new_revision')
        }),
        ('Dynamic Content (Editable JSON)', {
            'fields': ('details_of_change', 'impact_analysis', 'action_plan'),
            'description': 'Raw JSON fields for structured storage. Edit carefully.'
        }),
        ('Visual Content Summary (Read-Only)', {
            'fields': ('formatted_details_of_change', 'formatted_impact_analysis', 'formatted_action_plan'),
            'description': 'Formatted tables showing the structural details of ECN components.'
        }),
        ('Approvals', {
            'fields': ('initiator', 'reviewed_by', 'approved_by')
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formatted_details_of_change(self, obj):
        if not obj.details_of_change or not isinstance(obj.details_of_change, list):
            return "-"
        html = '<table style="width:100%; border: 1px solid #ccc; border-collapse: collapse; font-size: 13px;">'
        html += '<tr style="background:#f3f3f3; text-align: left;"><th style="border: 1px solid #ccc; padding:6px; width: 10%;">Sr. No</th><th style="border: 1px solid #ccc; padding:6px; width: 45%;">Description</th><th style="border: 1px solid #ccc; padding:6px; width: 45%;">Reason</th></tr>'
        for item in obj.details_of_change:
            sr = item.get('sr_no', '')
            desc = item.get('description', '')
            reason = item.get('reason', '')
            html += f'<tr><td style="border: 1px solid #ccc; padding:6px;">{sr}</td><td style="border: 1px solid #ccc; padding:6px;">{desc}</td><td style="border: 1px solid #ccc; padding:6px;">{reason}</td></tr>'
        html += '</table>'
        return format_html(html)
    formatted_details_of_change.short_description = "Formatted Details of Change"

    def formatted_impact_analysis(self, obj):
        if not obj.impact_analysis or not isinstance(obj.impact_analysis, list):
            return "-"
        html = '<table style="width:100%; border: 1px solid #ccc; border-collapse: collapse; font-size: 13px;">'
        html += '<tr style="background:#f3f3f3; text-align: left;"><th style="border: 1px solid #ccc; padding:6px; width: 40%;">Impact Item</th><th style="border: 1px solid #ccc; padding:6px; width: 20%;">Selection</th><th style="border: 1px solid #ccc; padding:6px; width: 40%;">Remarks</th></tr>'
        for item in obj.impact_analysis:
            name = item.get('name', '')
            selection = item.get('selection', '')
            remarks = item.get('remarks', '')
            html += f'<tr><td style="border: 1px solid #ccc; padding:6px;">{name}</td><td style="border: 1px solid #ccc; padding:6px;">{selection}</td><td style="border: 1px solid #ccc; padding:6px;">{remarks}</td></tr>'
        html += '</table>'
        return format_html(html)
    formatted_impact_analysis.short_description = "Formatted Impact Analysis"

    def formatted_action_plan(self, obj):
        if not obj.action_plan or not isinstance(obj.action_plan, list):
            return "-"
        html = '<table style="width:100%; border: 1px solid #ccc; border-collapse: collapse; font-size: 13px;">'
        html += '<tr style="background:#f3f3f3; text-align: left;"><th style="border: 1px solid #ccc; padding:6px; width: 40%;">Action</th><th style="border: 1px solid #ccc; padding:6px; width: 20%;">Responsible</th><th style="border: 1px solid #ccc; padding:6px; width: 15%;">Target Date</th><th style="border: 1px solid #ccc; padding:6px; width: 25%;">Remark</th></tr>'
        for item in obj.action_plan:
            action = item.get('action', '')
            responsible = item.get('responsible', '')
            target_date = item.get('target_date', '')
            remark = item.get('remark', '')
            html += f'<tr><td style="border: 1px solid #ccc; padding:6px;">{action}</td><td style="border: 1px solid #ccc; padding:6px;">{responsible}</td><td style="border: 1px solid #ccc; padding:6px;">{target_date}</td><td style="border: 1px solid #ccc; padding:6px;">{remark}</td></tr>'
        html += '</table>'
        return format_html(html)
    formatted_action_plan.short_description = "Formatted Action Plan"
